# Tool Integration Architecture Research

**Created**: 2025-12-05
**Context**: IRIS native client tool integration decisions
**Status**: Research complete, ready for implementation

---

## Executive Summary

This document captures research on tool integration options for IRIS, comparing native Ollama function calling vs MCP (Model Context Protocol). The recommended approach is a **hybrid strategy**: native Ollama tools for local functionality (bundled in .deb), MCP via lazy-mcp proxy for remote services (CITADEL).

**Key Finding**: lazy-mcp reduces token overhead by ~95% (from ~15,000 to ~800 tokens for 30 tools), making MCP viable for context-sensitive voice conversations.

---

## 1. Ollama Tool Calling

### How It Works

Tools are defined as JSON objects passed in the `tools` array to `/api/chat`:

```json
{
  "model": "qwen2.5:7b",
  "messages": [{"role": "user", "content": "What time is it?"}],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "Get the current time",
        "parameters": {
          "type": "object",
          "required": ["timezone"],
          "properties": {
            "timezone": {"type": "string", "description": "IANA timezone"}
          }
        }
      }
    }
  ]
}
```

### Response Flow

1. **Model decides** if tool is needed → returns `tool_calls` array
2. **Your code executes** the actual tool function
3. **Return result** via message with `role: "tool"`
4. **Model incorporates** result into final response

### Supported Models

| Model | Tool Support | Notes |
|-------|-------------|-------|
| Llama 3.1 (8B/70B) | Excellent | Best overall, reliable tool calling |
| Qwen 2.5 (7B/14B) | Excellent | Strong function calling |
| Mistral (7B) | Good | Lower resource needs |
| Command-R+ | Good | Cohere's model |
| Firefunction v2 | Native | Purpose-built for function calling |

### Context Window Recommendation

Ollama blog recommends using **32k+ context window** for better tool-calling performance. This increases memory usage but improves reliability.

---

## 2. Token Impact Analysis

### How Tools Consume Tokens

Tool definitions are serialized into the prompt as JSON schema:

| Tool Complexity | Tokens/Tool | Example |
|-----------------|-------------|---------|
| Simple (1-2 params) | ~50-80 | `get_time(timezone)` |
| Medium (3-5 params) | ~100-150 | `search(query, limit, type)` |
| Complex (nested) | ~200-400 | `create_order(items[], address{})` |

### Scaling Impact

| # Tools | Est. Token Overhead | Context Impact (32k) |
|---------|---------------------|----------------------|
| 2 tools | ~100-200 tokens | 0.5% - Negligible |
| 20 tools | ~1,000-2,000 tokens | 3-6% - Moderate |
| 100 tools | ~5,000-10,000 tokens | 15-30% - Significant |

### Optimization Strategies

1. **Lazy loading**: Only include relevant tools per query type
2. **Tool groups**: Let model choose category first, then specific tool
3. **Compact schemas**: Minimize descriptions, use short param names
4. **Flatten nested schemas**: Reduces complexity and improves generation quality

---

## 3. MCP vs Native Ollama Tools

### Architecture Comparison

```
NATIVE OLLAMA TOOLS:
User → Ollama → Tool Definition → Model → tool_calls → Your Code → Ollama
                    (inline JSON)                      (direct execution)

MCP TOOLS:
User → Ollama → MCP Client → MCP Server → Tool Execution → Response
                (bridge)     (separate process/HTTP)
```

### Latency Comparison

| Approach | Overhead | Notes |
|----------|----------|-------|
| Native Ollama tools | ~0ms | Tool defs inline, execution is your code |
| Local MCP (stdio) | ~5-20ms | Process communication overhead |
| Remote MCP (HTTP) | ~50-200ms+ | Network round-trip, depends on server |
| Remote MCP (cached) | ~10-50ms | With `cache_tools_list=True` |

### When to Use Each

**Use Native Ollama Tools when:**
- Low latency is critical (voice assistant!)
- Tools are simple and local
- You control all tool implementations
- Bundling in .deb package

**Use MCP Tools when:**
- Connecting to external services (Star Atlas, CITADEL)
- Tool definitions change frequently
- Want standardized interface across multiple LLM providers
- Complex integrations (databases, APIs, file systems)

---

## 4. lazy-mcp: 95% Token Reduction

### The Problem

When connecting to MCP servers directly:
- 30 tools = ~15,000 tokens in context at startup
- Every conversation starts with massive tool overhead
- Context window fills up fast

### lazy-mcp Solution

[lazy-mcp-preload](https://github.com/iamsamuelrodda/lazy-mcp-preload) is a proxy that:
1. Exposes only **2 meta-tools** to the LLM (~800 tokens)
2. Lazy-loads full tool schemas on-demand
3. Pre-warms servers in background for zero cold-start latency

### Token Savings

| Metric | Direct MCP | lazy-mcp | lazy-mcp-preload |
|--------|------------|----------|------------------|
| **Startup tokens** | ~15,000 | ~800 | ~800 |
| **First-call latency** | 0ms | ~500ms | ~0ms |
| **Tools visible** | 30 | 2 | 2 |
| **Context reduction** | baseline | **~95%** | **~95%** |

### The 2 Meta-Tools

1. **`get_tools_in_category(path)`** - Browse tool hierarchy
2. **`execute_tool(tool_path, arguments)`** - Run any tool

The LLM first explores categories, then calls specific tools - similar to how humans browse menus.

### Relevance for IRIS

If IRIS connects to MCP servers (e.g., CITADEL) via a bridge:
- Use lazy-mcp pattern to reduce token overhead
- Pre-warm servers to eliminate latency penalty
- Keep context lean for voice conversations

For native Ollama tools (local), lazy-mcp isn't needed since tool definitions are already minimal.

---

## 5. IRIS Tool Strategy

### Recommended Hybrid Approach

```
┌─────────────────────────────────────────────────────────┐
│                IRIS Client                              │
├─────────────────────────────────────────────────────────┤
│  LOCAL TOOLS (Native Ollama)                            │
│  • get_time() - bundled in .deb                         │
│  • calculator() - bundled in .deb                       │
│  • timer_reminder() - bundled in .deb                   │
│  → Direct execution, 0ms overhead                       │
├─────────────────────────────────────────────────────────┤
│  REMOTE TOOLS (MCP via lazy-mcp proxy)                  │
│  • web_search() - DuckDuckGo API                        │
│  • star_atlas_fleet() - CITADEL MCP                     │
│  • market_prices() - CITADEL MCP                        │
│  → ~800 tokens overhead, servers pre-warmed             │
└─────────────────────────────────────────────────────────┘
```

### Implementation Phases

**Phase 1: Local Tools (Current)**
- Native Ollama tool calling
- Simple tools: time, calculator, timer
- No external dependencies
- Bundled in .deb

**Phase 2: Remote Tools (When CITADEL Ready)**
- MCP client integration via lazy-mcp proxy
- Connect to CITADEL MCP server
- Web search via HTTP API
- Cache tool definitions, pre-warm servers

### Token Budget

For IRIS voice conversations (latency-sensitive):
- Target: <10 native tools active at once (~500-800 tokens)
- Remote tools via lazy-mcp: +800 tokens for meta-tools
- Total budget: ~1,500 tokens for tool definitions
- Leaves plenty of context for conversation history

---

## 6. Implementation Reference

### Native Ollama Tools (Python)

```python
import requests
from datetime import datetime
import pytz

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get current time in a timezone",
            "parameters": {
                "type": "object",
                "required": ["timezone"],
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone (e.g. Australia/Brisbane)"
                    }
                }
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "get_current_time": lambda tz: datetime.now(pytz.timezone(tz)).strftime("%I:%M %p")
}

def call_with_tools(prompt: str, messages: list):
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:7b",
            "messages": messages,
            "tools": TOOLS,
            "stream": False
        }
    ).json()

    if "tool_calls" in response["message"]:
        for tool_call in response["message"]["tool_calls"]:
            name = tool_call["function"]["name"]
            args = tool_call["function"]["arguments"]
            result = TOOL_FUNCTIONS[name](**args)

            messages.append(response["message"])
            messages.append({"role": "tool", "content": result})

        return call_with_tools("", messages)  # Get final response

    return response["message"]["content"]
```

---

## Sources

- [Ollama Tool Calling Docs](https://docs.ollama.com/capabilities/tool-calling)
- [Ollama Tool Support Blog](https://ollama.com/blog/tool-support)
- [Ollama Streaming Tools Blog](https://ollama.com/blog/streaming-tool)
- [Best Ollama Models for Function Calling 2025](https://collabnix.com/best-ollama-models-for-function-calling-tools-complete-guide-2025/)
- [MCP vs APIs for AI Agents](https://www.tinybird.co/blog/mcp-vs-apis-when-to-use-which-for-ai-agent-development)
- [MCP vs LLM Function Calling - Neon](https://neon.com/blog/mcp-vs-llm-function-calling)
- [Token Efficiency - Microsoft](https://medium.com/data-science-at-microsoft/token-efficiency-with-structured-output-from-language-models-be2e51d3d9d5)
- [lazy-mcp-preload](https://github.com/iamsamuelrodda/lazy-mcp-preload)
- [ollama-mcp-bridge](https://github.com/patruff/ollama-mcp-bridge)
- [ollama-mcp-client](https://github.com/mihirrd/ollama-mcp-client)
