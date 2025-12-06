"""
IRIS Native Tools - Ollama tool calling integration.

Tools are defined as JSON schemas and executed locally.
MCP tools (external services) are accessed via lazy-mcp bridge.

Pattern from: specs/RESEARCH-tool-integration-architecture.md

Usage:
    from src.tools import get_all_tools, execute_tool

    # Get all available tools (native + MCP if available)
    tools = get_all_tools()

    # Pass tools to Ollama /api/chat
    # If response has tool_calls, execute them:
    result = execute_tool(tool_name, arguments)

Tool Types:
    - Native: todo_*, get_current_time, calculate, web_search, memory_*
    - MCP: mcp_* (via lazy-mcp proxy to external services)
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

from src.search_providers import web_search as _search_provider_search

logger = logging.getLogger(__name__)


def _load_secrets() -> dict[str, str]:
    """Load secrets from ~/.config/iris/secrets.env if it exists."""
    secrets = {}
    secrets_path = Path.home() / ".config" / "iris" / "secrets.env"

    if secrets_path.exists():
        try:
            with open(secrets_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        secrets[key.strip()] = value.strip()
            logger.info(f"[Tools] Loaded secrets from {secrets_path}")
        except Exception as e:
            logger.warning(f"[Tools] Failed to load secrets: {e}")

    return secrets


# Load secrets from config file, fall back to environment variables
_secrets = _load_secrets()
BRAVE_API_KEY = _secrets.get("BRAVE_API_KEY") or os.environ.get("BRAVE_API_KEY", "")
TODOIST_API_TOKEN = (
    _secrets.get("TODOIST_API_TOKEN") or
    _secrets.get("TODOIST_API_KEY") or
    os.environ.get("TODOIST_API_TOKEN") or
    os.environ.get("TODOIST_API_KEY") or
    ""
)


# ==============================================================================
# Rate Limiter (1 request per second, queue excess requests)
# ==============================================================================


class RateLimiter:
    """Thread-safe rate limiter that queues requests to enforce rate limits."""

    def __init__(self, min_interval: float = 1.0):
        """
        Args:
            min_interval: Minimum seconds between requests (default: 1.0)
        """
        self.min_interval = min_interval
        self._last_request_time = 0.0
        self._lock = threading.Lock()

    def wait(self) -> float:
        """
        Wait until we can make a request. Returns actual wait time in seconds.
        Thread-safe: multiple agents calling this will be queued properly.
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            wait_time = max(0.0, self.min_interval - elapsed)

            if wait_time > 0:
                logger.info(f"[RateLimiter] Waiting {wait_time:.2f}s before request")
                time.sleep(wait_time)

            self._last_request_time = time.time()
            return wait_time


# Global rate limiter for web search (1 request per second)
_web_search_limiter = RateLimiter(min_interval=1.0)


# ==============================================================================
# Quota Tracker (threshold alerts at 20%, 5%, 0%)
# ==============================================================================

QUOTA_FILE = Path.home() / ".config" / "iris" / "quota.json"
MONTHLY_QUOTA = 2000  # Free tier limit
ALERT_THRESHOLDS = [0.20, 0.05, 0.0]  # Alert at 20%, 5%, 0% remaining


def _load_quota() -> dict:
    """Load quota tracking data from file."""
    if QUOTA_FILE.exists():
        try:
            with open(QUOTA_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[Quota] Failed to load quota file: {e}")
    return {}


def _save_quota(data: dict) -> None:
    """Save quota tracking data to file."""
    try:
        QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(QUOTA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"[Quota] Failed to save quota file: {e}")


def _update_quota_from_headers(headers: dict) -> str | None:
    """
    Parse rate limit headers and update quota tracking.
    Returns alert message if threshold crossed, None otherwise.

    Headers from Brave API (comma-separated: per-second, monthly):
    - x-ratelimit-remaining: "0, 1997" (per-second remaining, monthly remaining)
    - x-ratelimit-reset: "1, 2254307" (per-second reset, monthly reset)
    - x-ratelimit-policy: "1;w=1, 2000;w=2678400" (1/sec, 2000/31-days)
    """
    remaining_header = headers.get("x-ratelimit-remaining")
    reset_header = headers.get("x-ratelimit-reset")
    policy_header = headers.get("x-ratelimit-policy", "")

    if remaining_header is None:
        return None

    try:
        # Parse comma-separated values (per-second, monthly)
        remaining_parts = [x.strip() for x in remaining_header.split(",")]
        remaining = int(remaining_parts[1]) if len(remaining_parts) > 1 else int(remaining_parts[0])

        reset_parts = [x.strip() for x in reset_header.split(",")] if reset_header else []
        reset_time = reset_parts[1] if len(reset_parts) > 1 else (reset_parts[0] if reset_parts else None)
    except (ValueError, IndexError):
        return None

    # Parse policy to get monthly limit (second value)
    monthly_limit = MONTHLY_QUOTA
    if policy_header:
        try:
            policy_parts = [x.strip() for x in policy_header.split(",")]
            if len(policy_parts) > 1:
                # Second part: "2000;w=2678400"
                monthly_limit = int(policy_parts[1].split(";")[0])
            elif ";" in policy_parts[0]:
                monthly_limit = int(policy_parts[0].split(";")[0])
        except (ValueError, IndexError):
            pass

    # Calculate percentage remaining
    percent_remaining = remaining / monthly_limit if monthly_limit > 0 else 0

    # Load current quota data
    quota_data = _load_quota()
    last_alerted = quota_data.get("last_alerted_threshold", 1.0)

    # Convert reset_time from seconds to human-readable date
    reset_date = None
    if reset_time:
        try:
            reset_seconds = int(reset_time)
            reset_datetime = datetime.now() + timedelta(seconds=reset_seconds)
            reset_date = reset_datetime.strftime("%Y-%m-%d")
        except ValueError:
            reset_date = reset_time

    # Update quota data
    quota_data["remaining"] = remaining
    quota_data["monthly_limit"] = monthly_limit
    quota_data["percent_remaining"] = round(percent_remaining, 4)
    quota_data["reset_seconds"] = reset_time
    quota_data["reset_date"] = reset_date
    quota_data["last_updated"] = datetime.now().isoformat()

    # Check for threshold alerts (only alert once per threshold)
    alert_msg = None
    for threshold in ALERT_THRESHOLDS:
        if percent_remaining <= threshold < last_alerted:
            quota_data["last_alerted_threshold"] = threshold
            if threshold == 0.0:
                alert_msg = f"\n\n⚠️ QUOTA EXHAUSTED: 0 web searches remaining. Resets on {reset_date}."
            else:
                pct = int(threshold * 100)
                alert_msg = f"\n\n⚠️ QUOTA WARNING: Only {remaining} web searches remaining ({pct}% of monthly limit)."
            break

    _save_quota(quota_data)

    logger.info(f"[Quota] {remaining}/{monthly_limit} searches remaining ({percent_remaining:.1%})")

    return alert_msg


def get_quota_status() -> dict:
    """Get current quota status. Useful for status displays."""
    return _load_quota()


# ==============================================================================
# Session Todo List (Internal Task Tracking)
# ==============================================================================

# Session-scoped todo list - cleared on restart, used for multi-step tasks
_session_todos: list[dict] = []


def _todo_add(task: str, priority: str = "normal") -> str:
    """Add a task to the session todo list."""
    todo = {
        "id": len(_session_todos) + 1,
        "task": task,
        "status": "pending",
        "priority": priority,
        "created": time.time(),
    }
    _session_todos.append(todo)
    logger.info(f"[Todo] Added: {task}")
    return f"Added task #{todo['id']}: {task}"


def _todo_complete(task_id: int) -> str:
    """Mark a task as complete."""
    for todo in _session_todos:
        if todo["id"] == task_id:
            todo["status"] = "completed"
            logger.info(f"[Todo] Completed: {todo['task']}")
            return f"Completed task #{task_id}: {todo['task']}"
    return f"Task #{task_id} not found"


def _todo_list() -> str:
    """List all tasks in the session."""
    if not _session_todos:
        return "No tasks in the current session."

    lines = ["Current tasks:"]
    for todo in _session_todos:
        status = "✓" if todo["status"] == "completed" else "○"
        priority_marker = "!" if todo["priority"] == "high" else ""
        lines.append(f"  {status} #{todo['id']}{priority_marker}: {todo['task']}")

    pending = sum(1 for t in _session_todos if t["status"] == "pending")
    completed = sum(1 for t in _session_todos if t["status"] == "completed")
    lines.append(f"\n{pending} pending, {completed} completed")

    return "\n".join(lines)


def _todo_clear() -> str:
    """Clear all tasks from the session."""
    count = len(_session_todos)
    _session_todos.clear()
    logger.info(f"[Todo] Cleared {count} tasks")
    return f"Cleared {count} tasks from session."


def get_session_todos() -> list[dict]:
    """Get raw todo list (for UI display)."""
    return _session_todos.copy()


# ==============================================================================
# Tool Definitions (JSON Schema for Ollama)
# ==============================================================================
#
# Architecture: Meta-tool router pattern (like lazy-mcp)
# - Tier 1: Core tools always loaded (~150 tokens)
# - Tier 2: Single meta-tool routes to 12 capabilities (~100 tokens)
# - Total: ~250 tokens (vs ~1,571 with inline definitions = 84% reduction)
#
# ==============================================================================

# Tier 1: Core tools - always useful, minimal overhead
CORE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get current time/date. Use for time, date, or day questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone (e.g., 'Australia/Brisbane')",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Math calculations: arithmetic, percentages, conversions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression (e.g., '2+2', '15% of 200')",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

# Tier 2: Meta-tool for grouped capabilities
IRIS_META_TOOL = {
    "type": "function",
    "function": {
        "name": "iris",
        "description": """Execute IRIS capabilities. Categories:
- search: Web search for current info (query, count?)
- tasks: Session task tracking (add/complete/list, task?, task_id?, priority?)
- reminders: Todoist persistent reminders (create/list/done, content?, due?, task_content?)
- memory: Remember/recall facts (remember/recall/forget/relate/summary, entity?, facts?, query?, from?, to?, relation?)""",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["search", "tasks", "reminders", "memory"],
                    "description": "Capability category",
                },
                "action": {
                    "type": "string",
                    "description": "Action: search=query | tasks=add,complete,list | reminders=create,list,done | memory=remember,recall,forget,relate,summary",
                },
                "params": {
                    "type": "object",
                    "description": "Action parameters as key-value pairs",
                },
            },
            "required": ["category", "action"],
        },
    },
}

# Combined tool list for Ollama
TOOLS = CORE_TOOLS + [IRIS_META_TOOL]

# Legacy inline tools (kept for reference/fallback, not exported by default)
TOOLS_LEGACY = "see git history"

# Models that support tool calling (prefix match)
TOOL_CAPABLE_MODELS = ["qwen2.5", "qwen2", "llama3.1", "llama3.2", "mistral", "mixtral"]


def supports_tools(model_name: str) -> bool:
    """Check if a model supports tool calling."""
    model_lower = model_name.lower()
    return any(model_lower.startswith(prefix) for prefix in TOOL_CAPABLE_MODELS)


# ==============================================================================
# Tool Implementations
# ==============================================================================


def _get_current_time(timezone: str | None = None) -> str:
    """Get current time, optionally in a specific timezone."""
    try:
        if timezone:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            tz_name = timezone
        else:
            now = datetime.now()
            tz_name = "local time"

        # Format: "3:45 PM on Friday, December 6th, 2025"
        day = now.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        time_str = now.strftime(f"%-I:%M %p on %A, %B {day}{suffix}, %Y")
        return f"It's {time_str} ({tz_name})"

    except Exception as e:
        logger.warning(f"[Tools] Timezone error: {e}")
        # Fallback to local time
        now = datetime.now()
        day = now.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        time_str = now.strftime(f"%-I:%M %p on %A, %B {day}{suffix}, %Y")
        return f"It's {time_str} (local time)"


def _calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        # Handle percentage syntax first: "15% of 200" -> "0.15 * 200"
        expr = expression.lower()
        if "% of" in expr:
            parts = expr.split("% of")
            if len(parts) == 2:
                try:
                    percent = float(parts[0].strip())
                    value = float(parts[1].strip())
                    result = (percent / 100) * value
                    return f"{expression} = {result:g}"
                except ValueError:
                    pass

        # Handle standalone percentage: "15%" -> 0.15
        if "%" in expression:
            expr = expression.replace("%", "/100")
        else:
            expr = expression

        # Sanitize: only allow safe characters for eval
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expr):
            return f"Cannot evaluate: expression contains invalid characters"

        # Evaluate safely (no builtins, limited scope)
        result = eval(expr, {"__builtins__": {}}, {})
        return f"{expression} = {result:g}"

    except ZeroDivisionError:
        return "Cannot divide by zero"
    except Exception as e:
        return f"Cannot calculate: {str(e)}"


def _web_search(query: str, count: int = 3) -> str:
    """
    Search the web using the configured provider.

    Supports multiple backends (SearXNG preferred, Brave fallback).
    See src/search_providers.py for implementation.
    """
    return _search_provider_search(query, count)


# ==============================================================================
# Todoist API (Direct REST)
# ==============================================================================

TODOIST_API_URL = "https://api.todoist.com/rest/v2"


def _todoist_create_task(content: str, due_string: str = None, priority: int = 1) -> str:
    """Create a task in Todoist."""
    if not TODOIST_API_TOKEN:
        return "Todoist not configured. Add TODOIST_API_TOKEN to ~/.config/iris/secrets.env"

    try:
        payload = {"content": content}
        if due_string:
            payload["due_string"] = due_string
        if priority and priority > 1:
            payload["priority"] = priority

        response = requests.post(
            f"{TODOIST_API_URL}/tasks",
            headers={"Authorization": f"Bearer {TODOIST_API_TOKEN}"},
            json=payload,
            timeout=10,
        )

        if response.status_code == 200:
            task = response.json()
            due_info = ""
            if task.get("due"):
                due_info = f" (due: {task['due'].get('string', task['due'].get('date', ''))})"
            return f"Created task: {task['content']}{due_info}"
        else:
            logger.error(f"[Tools] Todoist error: {response.status_code} {response.text}")
            return f"Failed to create task (HTTP {response.status_code})"

    except Exception as e:
        logger.error(f"[Tools] Todoist error: {e}")
        return f"Todoist error: {str(e)}"


def _todoist_list_tasks(filter_str: str = None) -> str:
    """List tasks from Todoist."""
    if not TODOIST_API_TOKEN:
        return "Todoist not configured. Add TODOIST_API_TOKEN to ~/.config/iris/secrets.env"

    try:
        params = {}
        if filter_str:
            params["filter"] = filter_str

        response = requests.get(
            f"{TODOIST_API_URL}/tasks",
            headers={"Authorization": f"Bearer {TODOIST_API_TOKEN}"},
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            tasks = response.json()
            if not tasks:
                return "No tasks found."

            lines = [f"You have {len(tasks)} task(s):"]
            for i, task in enumerate(tasks[:10], 1):  # Limit to 10 for voice
                due = ""
                if task.get("due"):
                    due = f" - due {task['due'].get('string', task['due'].get('date', ''))}"
                lines.append(f"{i}. {task['content']}{due}")

            if len(tasks) > 10:
                lines.append(f"...and {len(tasks) - 10} more")

            return "\n".join(lines)
        else:
            return f"Failed to get tasks (HTTP {response.status_code})"

    except Exception as e:
        logger.error(f"[Tools] Todoist error: {e}")
        return f"Todoist error: {str(e)}"


def _todoist_complete_task(task_id: str = None, task_content: str = None) -> str:
    """Complete a task in Todoist by ID or by searching content."""
    if not TODOIST_API_TOKEN:
        return "Todoist not configured. Add TODOIST_API_TOKEN to ~/.config/iris/secrets.env"

    try:
        # If no ID given, try to find by content
        if not task_id and task_content:
            response = requests.get(
                f"{TODOIST_API_URL}/tasks",
                headers={"Authorization": f"Bearer {TODOIST_API_TOKEN}"},
                timeout=10,
            )
            if response.status_code == 200:
                tasks = response.json()
                for task in tasks:
                    if task_content.lower() in task["content"].lower():
                        task_id = task["id"]
                        break

        if not task_id:
            return "Could not find task to complete. Please specify the task."

        response = requests.post(
            f"{TODOIST_API_URL}/tasks/{task_id}/close",
            headers={"Authorization": f"Bearer {TODOIST_API_TOKEN}"},
            timeout=10,
        )

        if response.status_code == 204:
            return "Task completed!"
        else:
            return f"Failed to complete task (HTTP {response.status_code})"

    except Exception as e:
        logger.error(f"[Tools] Todoist error: {e}")
        return f"Todoist error: {str(e)}"


# ==============================================================================
# Memory API (Knowledge Graph)
# ==============================================================================

# Lazy-load memory module to avoid import errors during warmup
_memory_manager = None


def _get_memory_manager():
    """Get or create the memory manager (lazy initialization)."""
    global _memory_manager
    if _memory_manager is None:
        try:
            from src.memory import get_memory_manager
            _memory_manager = get_memory_manager(user_id="default")
            logger.info("[Memory] Initialized knowledge graph")
        except Exception as e:
            logger.error(f"[Memory] Failed to initialize: {e}")
            raise
    return _memory_manager


def _memory_remember(entity_name: str, facts: list[str], entity_type: str = "concept") -> str:
    """Remember facts about an entity."""
    try:
        mm = _get_memory_manager()

        # Create or update entity with observations
        result = mm.create_entities([{
            "name": entity_name,
            "entityType": entity_type,
            "observations": facts,
        }], is_user_edit=True)

        if result:
            entity = result[0]
            fact_count = len(entity.observations)
            if fact_count > 0:
                return f"Remembered {fact_count} fact(s) about {entity_name}."
            else:
                return f"Entity '{entity_name}' already exists. Added new facts."
        else:
            return f"Could not remember information about {entity_name}."

    except Exception as e:
        logger.error(f"[Memory] Remember error: {e}")
        return f"Memory error: {str(e)}"


def _memory_recall(query: str) -> str:
    """Search memory for information."""
    try:
        mm = _get_memory_manager()

        # Search for matching entities
        results = mm.search_nodes(query, limit=5)

        if not results:
            return f"I don't have any memories matching '{query}'."

        lines = [f"Here's what I remember about '{query}':"]
        for entity in results:
            lines.append(f"\n**{entity.name}** ({entity.entity_type}):")
            for obs in entity.observations:
                lines.append(f"  - {obs}")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"[Memory] Recall error: {e}")
        return f"Memory error: {str(e)}"


def _memory_forget(entity_name: str) -> str:
    """Forget an entity and all its facts."""
    try:
        mm = _get_memory_manager()

        deleted = mm.delete_entities([entity_name])

        if deleted:
            return f"Forgot everything about {entity_name}."
        else:
            return f"I don't have any memories of '{entity_name}'."

    except Exception as e:
        logger.error(f"[Memory] Forget error: {e}")
        return f"Memory error: {str(e)}"


def _memory_relate(from_entity: str, relation: str, to_entity: str) -> str:
    """Create a relationship between two entities."""
    try:
        mm = _get_memory_manager()

        # Create relation
        created = mm.create_relations([{
            "from": from_entity,
            "to": to_entity,
            "relationType": relation,
        }])

        if created:
            return f"Noted: {from_entity} {relation} {to_entity}."
        else:
            return f"Relationship already exists or could not be created."

    except Exception as e:
        logger.error(f"[Memory] Relate error: {e}")
        return f"Memory error: {str(e)}"


def _memory_summary() -> str:
    """Get a summary of the user's memory graph."""
    try:
        mm = _get_memory_manager()

        # Get the full graph
        graph = mm.read_graph()

        if not graph.entities:
            return "I don't have any stored memories yet."

        # Build summary
        entity_count = len(graph.entities)
        relation_count = len(graph.relations)
        total_facts = sum(len(e.observations) for e in graph.entities)

        lines = [f"I remember {entity_count} thing(s) with {total_facts} fact(s) and {relation_count} relationship(s):\n"]

        for entity in graph.entities[:10]:  # Limit for voice output
            fact_preview = entity.observations[0][:50] + "..." if entity.observations else "no details"
            lines.append(f"- **{entity.name}**: {fact_preview}")

        if len(graph.entities) > 10:
            lines.append(f"\n...and {len(graph.entities) - 10} more.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"[Memory] Summary error: {e}")
        return f"Memory error: {str(e)}"


# ==============================================================================
# Meta-Tool Router (iris)
# ==============================================================================

def _iris_router(category: str, action: str, params: dict = None) -> str:
    """
    Route meta-tool calls to actual implementations.

    This is the core of the lazy-loading pattern - one tool definition
    routes to 12 different capabilities based on category+action.
    """
    params = params or {}

    logger.info(f"[IRIS] Routing: {category}/{action} with {params}")

    # Search category
    if category == "search":
        if action == "query" or action == "search":
            return _web_search(
                query=params.get("query", ""),
                count=params.get("count", 3)
            )
        return f"Unknown search action: {action}. Use: query"

    # Tasks category (session todos)
    elif category == "tasks":
        if action == "add":
            return _todo_add(
                task=params.get("task", params.get("content", "")),
                priority=params.get("priority", "normal")
            )
        elif action == "complete":
            task_id = params.get("task_id", params.get("id", 0))
            if isinstance(task_id, str):
                task_id = int(task_id) if task_id.isdigit() else 0
            return _todo_complete(task_id=task_id)
        elif action == "list":
            return _todo_list()
        return f"Unknown tasks action: {action}. Use: add, complete, list"

    # Reminders category (Todoist)
    elif category == "reminders":
        if action == "create":
            return _todoist_create_task(
                content=params.get("content", ""),
                due_string=params.get("due", params.get("due_string")),
                priority=params.get("priority", 1)
            )
        elif action == "list":
            return _todoist_list_tasks(
                filter_str=params.get("filter", params.get("filter_str"))
            )
        elif action == "done" or action == "complete":
            return _todoist_complete_task(
                task_content=params.get("task_content", params.get("content", ""))
            )
        return f"Unknown reminders action: {action}. Use: create, list, done"

    # Memory category (knowledge graph)
    elif category == "memory":
        if action == "remember":
            facts = params.get("facts", [])
            if isinstance(facts, str):
                facts = [facts]
            return _memory_remember(
                entity_name=params.get("entity", params.get("entity_name", "User")),
                facts=facts,
                entity_type=params.get("type", params.get("entity_type", "concept"))
            )
        elif action == "recall":
            return _memory_recall(
                query=params.get("query", "")
            )
        elif action == "forget":
            return _memory_forget(
                entity_name=params.get("entity", params.get("entity_name", ""))
            )
        elif action == "relate":
            return _memory_relate(
                from_entity=params.get("from", params.get("from_entity", "")),
                relation=params.get("relation", ""),
                to_entity=params.get("to", params.get("to_entity", ""))
            )
        elif action == "summary":
            return _memory_summary()
        return f"Unknown memory action: {action}. Use: remember, recall, forget, relate, summary"

    return f"Unknown category: {category}. Use: search, tasks, reminders, memory"


# ==============================================================================
# Tool Execution
# ==============================================================================

# Map tool names to functions (core tools + meta-tool router)
TOOL_FUNCTIONS = {
    # Tier 1: Core tools (always inline)
    "get_current_time": _get_current_time,
    "calculate": _calculate,
    # Tier 2: Meta-tool router
    "iris": _iris_router,
    # Legacy direct access (for backwards compatibility)
    "web_search": _web_search,
    "todo_add": _todo_add,
    "todo_complete": _todo_complete,
    "todo_list": _todo_list,
    "todoist_create_task": _todoist_create_task,
    "todoist_list_tasks": _todoist_list_tasks,
    "todoist_complete_task": _todoist_complete_task,
    "memory_remember": _memory_remember,
    "memory_recall": _memory_recall,
    "memory_forget": _memory_forget,
    "memory_relate": _memory_relate,
    "memory_summary": _memory_summary,
}


def get_tool_names() -> list[str]:
    """Get list of available tool names (meta-tool categories)."""
    return ["get_current_time", "calculate", "iris(search|tasks|reminders|memory)"]


# ==============================================================================
# Unified Tool Access (Native + MCP)
# ==============================================================================

def get_all_tools(include_mcp: bool = True) -> list[dict]:
    """
    Get all available tools (native + MCP if available).

    Args:
        include_mcp: If True, include MCP tools when lazy-mcp is running

    Returns:
        List of tool definitions for Ollama
    """
    all_tools = TOOLS.copy()

    if include_mcp:
        try:
            from src.mcp_bridge import get_mcp_tools
            mcp_tools = get_mcp_tools()
            all_tools.extend(mcp_tools)
            if mcp_tools:
                logger.info(f"[Tools] Added {len(mcp_tools)} MCP tools")
        except ImportError:
            logger.debug("[Tools] MCP bridge not available")
        except Exception as e:
            logger.warning(f"[Tools] Failed to load MCP tools: {e}")

    return all_tools


def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """
    Execute a tool by name with given arguments.

    Handles both native tools and MCP tools (mcp_* prefix).

    Args:
        name: Tool name (native or MCP)
        arguments: Dict of arguments to pass to the tool

    Returns:
        Tool result as a string
    """
    # Check if this is an MCP tool
    if name.startswith("mcp_"):
        try:
            from src.mcp_bridge import execute_mcp_tool
            logger.info(f"[Tools] Executing MCP tool: {name}({arguments})")
            result = execute_mcp_tool(name, arguments)
            logger.info(f"[Tools] MCP result: {result[:100]}...")
            return result
        except ImportError:
            return "MCP tools not available (mcp_bridge module not found)"
        except Exception as e:
            logger.error(f"[Tools] MCP error: {e}")
            return f"MCP tool failed: {str(e)}"

    # Native tool execution
    if name not in TOOL_FUNCTIONS:
        logger.warning(f"[Tools] Unknown tool: {name}")
        return f"Error: Unknown tool '{name}'"

    try:
        logger.info(f"[Tools] Executing {name}({arguments})")
        result = TOOL_FUNCTIONS[name](**arguments)
        logger.info(f"[Tools] Result: {result}")
        return result
    except Exception as e:
        logger.error(f"[Tools] Error executing {name}: {e}")
        return f"Error executing {name}: {str(e)}"


# ==============================================================================
# Testing
# ==============================================================================

if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("TOOL CONTEXT ANALYSIS")
    print("=" * 60)

    # Measure token overhead
    import json
    total_chars = 0
    for tool in TOOLS:
        tool_json = json.dumps(tool)
        chars = len(tool_json)
        total_chars += chars
        name = tool['function']['name']
        print(f"  {name:20} {chars:4} chars")

    print(f"\n  TOTAL: {total_chars:,} chars (~{total_chars // 4:,} tokens)")
    print(f"  Tools: {len(TOOLS)}")

    print("\n" + "=" * 60)
    print("CORE TOOLS TEST")
    print("=" * 60)
    print(f"  Time: {execute_tool('get_current_time', {})}")
    print(f"  Calc: {execute_tool('calculate', {'expression': '15% of 200'})}")

    print("\n" + "=" * 60)
    print("META-TOOL ROUTER TEST (iris)")
    print("=" * 60)

    # Test search via router
    print("\n[Search Category]")
    result = execute_tool('iris', {
        'category': 'search',
        'action': 'query',
        'params': {'query': 'test', 'count': 1}
    })
    print(f"  iris(search/query): {result[:80]}...")

    # Test tasks via router
    print("\n[Tasks Category]")
    print(f"  iris(tasks/add): {execute_tool('iris', {'category': 'tasks', 'action': 'add', 'params': {'task': 'Test task'}})}")
    print(f"  iris(tasks/list): {execute_tool('iris', {'category': 'tasks', 'action': 'list', 'params': {}})}")
    print(f"  iris(tasks/complete): {execute_tool('iris', {'category': 'tasks', 'action': 'complete', 'params': {'task_id': 1}})}")
    _session_todos.clear()

    # Test memory via router
    print("\n[Memory Category]")
    print(f"  iris(memory/remember): {execute_tool('iris', {'category': 'memory', 'action': 'remember', 'params': {'entity': 'Test', 'facts': ['fact1']}})}")
    print(f"  iris(memory/recall): {execute_tool('iris', {'category': 'memory', 'action': 'recall', 'params': {'query': 'test'}})}")
    print(f"  iris(memory/forget): {execute_tool('iris', {'category': 'memory', 'action': 'forget', 'params': {'entity': 'Test'}})}")

    print("\n" + "=" * 60)
    print("COMPARISON: Old vs New Token Usage")
    print("=" * 60)
    print(f"  Old (14 inline tools): ~1,571 tokens")
    print(f"  New (2 core + 1 meta):  ~{total_chars // 4} tokens")
    print(f"  Reduction: {100 - (total_chars // 4 / 1571 * 100):.0f}%")

    print(f"\nAvailable tools: {get_tool_names()}")
