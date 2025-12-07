#!/usr/bin/env python3
"""
End-to-End Discovery Tests for IRIS

Validates that IRIS:
1. Uses iris_discover when encountering unknown capabilities
2. Calls the correct tools after discovery
3. Speaks appropriate responses

Usage:
    python test_discovery_e2e.py
    python test_discovery_e2e.py --verbose
    python test_discovery_e2e.py --save-results results.jsonl
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Test Cases
# ==============================================================================

TEST_CASES = [
    {
        "id": "reminder-basic",
        "description": "Simple reminder request",
        "input": "Remind me to check fuel tomorrow",
        "expected_tools": ["iris"],  # Should call iris(reminders, create, ...)
        "expected_tool_params": {
            "category": "reminders",
            "action": "create",
        },
        "expected_response_contains": ["reminder", "fuel"],
        "should_use_discovery": False,  # Should know reminders directly
    },
    {
        "id": "reminder-unknown",
        "description": "Reminder with ambiguous phrasing",
        "input": "Set a reminder for budget review next week",
        "expected_tools": ["iris"],
        "expected_tool_params": {
            "category": "reminders",
            "action": "create",
        },
        "expected_response_contains": ["reminder", "budget"],
        "should_use_discovery": False,
    },
    {
        "id": "search-and-reminder",
        "description": "Multi-step: search + reminder",
        "input": "Search for Bitcoin news and remind me to check the price tomorrow",
        "expected_tools": ["todo_write", "iris", "iris"],  # todo_write + search + reminder
        "expected_response_contains": ["Bitcoin", "reminder"],
        "should_use_discovery": False,
    },
    {
        "id": "memory-basic",
        "description": "Memory storage request",
        "input": "Remember that I prefer mining ships",
        "expected_tools": ["iris"],
        "expected_tool_params": {
            "category": "memory",
            "action": "remember",
        },
        "expected_response_contains": ["remember", "mining"],
        "should_use_discovery": False,
    },
    {
        "id": "list-reminders",
        "description": "List all reminders",
        "input": "What are my reminders?",
        "expected_tools": ["iris"],
        "expected_tool_params": {
            "category": "reminders",
            "action": "list",
        },
        "expected_response_contains": [],  # Depends on actual reminders
        "should_use_discovery": False,
    },
]


# ==============================================================================
# E2E Test Harness
# ==============================================================================

class IRISTestHarness:
    """
    End-to-end test harness for IRIS.
    Simulates text input and captures tool calls + spoken output.
    """

    def __init__(self, model: str = "qwen2.5:7b", verbose: bool = False):
        self.model = model
        self.verbose = verbose
        self.ollama_url = "http://localhost:11434/api/chat"

        # Import IRIS components
        from src.tools import TOOLS, execute_tool
        self.tools = TOOLS
        self.execute_tool = execute_tool

        # Load system prompt
        from iris_local import get_system_prompt
        self.system_prompt = get_system_prompt(model, "normal")

    def run_conversation(self, user_input: str) -> dict[str, Any]:
        """
        Run a single conversation turn.

        Returns:
            {
                "user_input": str,
                "tool_calls": [{"name": str, "arguments": dict}, ...],
                "tool_results": [str, ...],
                "assistant_response": str,
                "tokens": {"prompt": int, "completion": int},
            }
        """
        logger.info(f"User: {user_input}")

        # Build messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]

        tool_calls = []
        tool_results = []
        conversation_history = messages.copy()

        # Multi-turn loop for tool calling
        max_turns = 5
        for turn in range(max_turns):
            # Call Ollama
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "messages": conversation_history,
                    "tools": self.tools,
                    "stream": False,
                },
                timeout=60,
            )

            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code} {response.text}")

            data = response.json()
            message = data["message"]

            # Check for tool calls
            if "tool_calls" in message and message["tool_calls"]:
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]

                    logger.info(f"Tool call: {tool_name}({tool_args})")
                    tool_calls.append({"name": tool_name, "arguments": tool_args})

                    # Execute tool
                    try:
                        result = self.execute_tool(tool_name, tool_args)
                        tool_results.append(result)
                        logger.info(f"Tool result: {result[:100]}...")
                    except Exception as e:
                        result = f"Error: {str(e)}"
                        tool_results.append(result)
                        logger.error(f"Tool error: {e}")

                    # Add tool result to conversation
                    conversation_history.append(message)
                    conversation_history.append({
                        "role": "tool",
                        "content": result,
                    })
            else:
                # Final response
                assistant_text = message.get("content", "")
                logger.info(f"IRIS: {assistant_text}")

                return {
                    "user_input": user_input,
                    "tool_calls": tool_calls,
                    "tool_results": tool_results,
                    "assistant_response": assistant_text,
                    "tokens": {
                        "prompt": data.get("prompt_eval_count", 0),
                        "completion": data.get("eval_count", 0),
                    },
                }

        # Max turns reached
        logger.warning(f"Max turns ({max_turns}) reached")
        return {
            "user_input": user_input,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "assistant_response": "(max turns reached)",
            "tokens": {"prompt": 0, "completion": 0},
        }


# ==============================================================================
# Test Validation
# ==============================================================================

def validate_test_case(test_case: dict, result: dict) -> dict:
    """
    Validate a test result against expectations.

    Returns:
        {
            "passed": bool,
            "failures": [str, ...],
            "warnings": [str, ...],
        }
    """
    failures = []
    warnings = []

    # Check tool calls
    if "expected_tools" in test_case:
        tool_names = [tc["name"] for tc in result["tool_calls"]]
        expected = test_case["expected_tools"]

        if len(tool_names) != len(expected):
            failures.append(
                f"Expected {len(expected)} tool calls, got {len(tool_names)}: {tool_names}"
            )
        else:
            for i, (actual, exp) in enumerate(zip(tool_names, expected)):
                if actual != exp:
                    failures.append(f"Tool call #{i+1}: expected {exp}, got {actual}")

    # Check tool parameters
    if "expected_tool_params" in test_case and result["tool_calls"]:
        # Find first iris call
        iris_calls = [tc for tc in result["tool_calls"] if tc["name"] == "iris"]
        if iris_calls:
            params = iris_calls[0]["arguments"]
            for key, expected_value in test_case["expected_tool_params"].items():
                if key not in params:
                    failures.append(f"Missing parameter: {key}")
                elif params[key] != expected_value:
                    failures.append(
                        f"Parameter {key}: expected {expected_value}, got {params[key]}"
                    )

    # Check response contains expected phrases
    if "expected_response_contains" in test_case:
        response_lower = result["assistant_response"].lower()
        for phrase in test_case["expected_response_contains"]:
            if phrase.lower() not in response_lower:
                warnings.append(f"Response missing phrase: '{phrase}'")

    # Check discovery usage
    if "should_use_discovery" in test_case:
        used_discovery = any(
            tc["name"] == "iris_discover" for tc in result["tool_calls"]
        )
        expected = test_case["should_use_discovery"]

        if used_discovery != expected:
            if expected:
                failures.append("Expected to use iris_discover, but didn't")
            else:
                warnings.append("Used iris_discover when not expected (may be ok)")

    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "warnings": warnings,
    }


# ==============================================================================
# Main Test Runner
# ==============================================================================

def run_tests(
    model: str = "qwen2.5:7b",
    verbose: bool = False,
    save_results: str | None = None,
) -> dict:
    """
    Run all test cases.

    Returns:
        {
            "summary": {"total": int, "passed": int, "failed": int},
            "results": [{test_case, result, validation}, ...],
        }
    """
    harness = IRISTestHarness(model=model, verbose=verbose)

    results = []
    passed = 0
    failed = 0

    logger.info(f"Running {len(TEST_CASES)} test cases...")
    logger.info("=" * 60)

    for i, test_case in enumerate(TEST_CASES, 1):
        logger.info(f"\n[{i}/{len(TEST_CASES)}] {test_case['id']}")
        logger.info(f"Description: {test_case['description']}")
        logger.info("-" * 60)

        try:
            # Run test
            result = harness.run_conversation(test_case["input"])

            # Validate
            validation = validate_test_case(test_case, result)

            # Record result
            test_result = {
                "test_case": test_case,
                "result": result,
                "validation": validation,
                "timestamp": datetime.now().isoformat(),
            }
            results.append(test_result)

            # Update counters
            if validation["passed"]:
                passed += 1
                logger.info("✓ PASSED")
            else:
                failed += 1
                logger.error("✗ FAILED")
                for failure in validation["failures"]:
                    logger.error(f"  - {failure}")

            # Show warnings
            for warning in validation["warnings"]:
                logger.warning(f"  ⚠ {warning}")

        except Exception as e:
            logger.error(f"✗ ERROR: {e}")
            failed += 1
            results.append({
                "test_case": test_case,
                "result": None,
                "validation": {
                    "passed": False,
                    "failures": [f"Exception: {str(e)}"],
                    "warnings": [],
                },
                "timestamp": datetime.now().isoformat(),
            })

        logger.info("-" * 60)

    # Summary
    summary = {
        "total": len(TEST_CASES),
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed / len(TEST_CASES) * 100:.1f}%",
    }

    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total:  {summary['total']}")
    logger.info(f"Passed: {summary['passed']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Rate:   {summary['pass_rate']}")

    # Save results
    if save_results:
        output_path = Path(save_results)
        with open(output_path, "w") as f:
            for result in results:
                f.write(json.dumps(result) + "\n")
        logger.info(f"\nResults saved to: {output_path}")

    return {
        "summary": summary,
        "results": results,
    }


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="E2E Discovery Tests for IRIS")
    parser.add_argument(
        "--model",
        default="qwen2.5:7b",
        help="Ollama model to use (default: qwen2.5:7b)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--save-results",
        metavar="FILE",
        help="Save results to JSONL file (e.g., results.jsonl)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run tests
    test_results = run_tests(
        model=args.model,
        verbose=args.verbose,
        save_results=args.save_results,
    )

    # Exit code
    sys.exit(0 if test_results["summary"]["failed"] == 0 else 1)
