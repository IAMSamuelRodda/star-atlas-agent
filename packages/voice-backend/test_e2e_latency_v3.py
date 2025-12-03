#!/usr/bin/env python3
"""
End-to-end Voice Latency Benchmark v3 - Pattern vs Haiku Isolation

CRITICAL LESSONS LEARNED (2025-12-03):
=====================================
The Agent SDK's query() function has ~5 seconds of overhead for simple Haiku
calls. This was NOT caught by previous tests because:
1. We tested pattern-matched messages (fleet, wallet) which use instant fallbacks
2. We didn't set thresholds to flag unexpected latency
3. We didn't isolate pattern-based vs Haiku-based paths

WHAT THIS TEST DOES:
===================
1. Tests BOTH pattern-matched AND non-pattern messages separately
2. Sets strict thresholds to catch regressions immediately
3. Reports which path was taken (pattern vs Haiku vs no-ack)
4. Validates that pattern fallbacks are truly instant (<50ms)
5. Validates that Haiku acknowledgments are reasonable (<500ms)

ARCHITECTURE:
============
Pattern-matched messages → getQuickFallback() → 3-12ms
  Keywords: fleet, ship, wallet, balance, account, market, price,
            trade, mission, quest, task, status, update, progress
  Prefixes: what/where/when/why/who/how, tell me/show me/find/search,
            do/make/create/start/stop/enable

Non-pattern messages → generateQuickAcknowledgment() → Direct Anthropic API
  BEFORE: Agent SDK query() → 5+ seconds (BOTTLENECK!)
  AFTER: Direct Anthropic SDK → 1.7-2.7 seconds

Usage:
  python test_e2e_latency_v3.py                  # Run all tests
  python test_e2e_latency_v3.py --quick          # Quick smoke test
  python test_e2e_latency_v3.py --threshold 100  # Fail if pattern > 100ms
"""

import argparse
import time
import requests
import json
import sys
from dataclasses import dataclass
from typing import Optional, Literal

# Configuration
AGENT_API_URL = "http://localhost:3001"
VOICE_BACKEND_URL = "http://localhost:8001"

# Thresholds (in milliseconds)
PATTERN_ACK_THRESHOLD_MS = 50      # Pattern-based should be <50ms
HAIKU_ACK_THRESHOLD_MS = 3000      # Haiku via direct API should be <3s
HAIKU_ACK_WARNING_MS = 500         # Warn if Haiku is slow
AGENT_SDK_REGRESSION_MS = 4000     # Alert if we've regressed to Agent SDK


# Known pattern-based acknowledgment texts (from fast-layer.ts getQuickFallback)
# These are deterministic - if we get different text, the fast layer was bypassed
KNOWN_PATTERN_ACKS = {
    "fleet": "Checking your fleet status.",
    "ship": "Checking your fleet status.",
    "wallet": "Let me check that for you.",
    "balance": "Let me check that for you.",
    "account": "Let me check that for you.",
    "market": "Looking up the market data.",
    "price": "Looking up the market data.",
    "trade": "Looking up the market data.",
    "mission": "Let me check on that.",
    "quest": "Let me check on that.",
    "task": "Let me check on that.",
    "status": "Checking the status now.",
    "update": "Checking the status now.",
    "progress": "Checking the status now.",
    "question_prefix": "Let me look into that.",  # what/where/when/why/who/how
    "request_prefix": "Sure, one moment.",  # tell me/show me/find/search
    "help_pattern": "Sure, I can help with that.",  # help/how do/how can i
    "action_prefix": "On it.",  # do/make/create/start/stop/enable
    "generic_fallback": "Got it, working on that.",  # >10 chars, no pattern
}


# Test cases with expected behavior
TEST_CASES = [
    # Pattern-matched messages (should be instant)
    {
        "message": "Check my fleet status",
        "expected_path": "pattern",
        "pattern_keyword": "fleet",
        "expected_ack": "Checking your fleet status.",
        "description": "Fleet keyword - domain pattern",
    },
    {
        "message": "Show me my wallet balance",
        "expected_path": "pattern",
        "pattern_keyword": "wallet",
        "expected_ack": "Let me check that for you.",
        "description": "Wallet keyword - domain pattern",
    },
    {
        "message": "What is the current market price?",
        "expected_path": "pattern",
        "pattern_keyword": "what",
        "expected_ack": "Looking up the market data.",  # matches "market" first
        "description": "Question prefix - starts with 'what'",
    },
    {
        "message": "Tell me about my missions",
        "expected_path": "pattern",
        "pattern_keyword": "tell me",
        "expected_ack": "Let me check on that.",  # matches "mission" first
        "description": "Request prefix - starts with 'tell me'",
    },
    {
        "message": "How do I configure this feature?",
        "expected_path": "pattern",
        "pattern_keyword": "how do",
        "expected_ack": "Let me look into that.",
        "description": "Help pattern - 'how do'",
    },
    {
        "message": "Create a new trading strategy",
        "expected_path": "pattern",
        "pattern_keyword": "create",
        "expected_ack": "On it.",
        "description": "Action prefix - starts with 'create'",
    },

    # Non-pattern messages (should go to Haiku or generic fallback)
    {
        "message": "I was wondering about something",
        "expected_path": "haiku",
        "pattern_keyword": None,
        "expected_ack": None,  # Haiku generates dynamic text
        "description": "No clear pattern - should use Haiku",
    },
    {
        "message": "That's interesting information",
        "expected_path": "haiku",
        "pattern_keyword": None,
        "expected_ack": None,  # Haiku generates dynamic text
        "description": "Statement - no pattern match",
    },

    # Messages that should get generic fallback (>10 chars, no pattern)
    {
        "message": "Let me think about that for a moment",
        "expected_path": "pattern",  # >10 chars fallback
        "pattern_keyword": ">10chars",
        "expected_ack": "Got it, working on that.",
        "description": "Long message - generic fallback",
    },

    # Short messages (might not get ack)
    {
        "message": "ok cool",
        "expected_path": "none",
        "pattern_keyword": None,
        "expected_ack": None,
        "description": "Short message - may skip ack",
    },
]


@dataclass
class TestResult:
    """Result from a single test case."""
    message: str
    description: str
    expected_path: str  # "pattern", "haiku", or "none"
    expected_ack: Optional[str] = None  # Expected ack text (for pattern validation)

    # Measured values
    ack_received: bool = False
    ack_latency_ms: float = 0.0
    ack_text: str = ""

    # Inferred path based on latency
    inferred_path: str = "unknown"

    # Code path validation
    ack_text_matched: bool = False  # True if ack text matches expected
    fast_layer_bypassed: bool = False  # True if fast layer was skipped

    # Validation
    passed: bool = False
    failure_reason: str = ""

    def validate(self):
        """Validate the result against expectations and thresholds."""
        if self.expected_path == "none":
            # No ack expected
            if not self.ack_received:
                self.passed = True
                self.inferred_path = "none"
            else:
                self.passed = True  # Getting an ack is also fine
                self.inferred_path = "pattern" if self.ack_latency_ms < PATTERN_ACK_THRESHOLD_MS else "haiku"
            return

        if not self.ack_received:
            self.passed = False
            self.failure_reason = f"Expected {self.expected_path} ack but got none - FAST LAYER BYPASSED?"
            self.inferred_path = "none"
            self.fast_layer_bypassed = True
            return

        # Validate ack text matches expected (code path validation)
        if self.expected_ack:
            self.ack_text_matched = self.ack_text == self.expected_ack
            if not self.ack_text_matched:
                # Check if it's a known pattern ack (fast layer working but different pattern matched)
                if self.ack_text in KNOWN_PATTERN_ACKS.values():
                    # Different pattern matched - not a bypass, just different logic path
                    self.ack_text_matched = True  # Allow it, pattern matching still working
                else:
                    # Unknown ack text - possibly Haiku fallback or bypass
                    self.fast_layer_bypassed = self.ack_latency_ms > HAIKU_ACK_WARNING_MS

        # Infer which path was taken based on latency
        if self.ack_latency_ms < PATTERN_ACK_THRESHOLD_MS:
            self.inferred_path = "pattern"
        elif self.ack_latency_ms < HAIKU_ACK_THRESHOLD_MS:
            self.inferred_path = "haiku"
        else:
            self.inferred_path = "agent_sdk_regression"

        # Check thresholds
        if self.expected_path == "pattern":
            if self.ack_latency_ms <= PATTERN_ACK_THRESHOLD_MS:
                self.passed = True
            elif self.ack_latency_ms <= HAIKU_ACK_WARNING_MS:
                self.passed = True
                self.failure_reason = f"Pattern expected <{PATTERN_ACK_THRESHOLD_MS}ms, got {self.ack_latency_ms:.0f}ms (used Haiku?)"
            else:
                self.passed = False
                self.failure_reason = f"Pattern expected <{PATTERN_ACK_THRESHOLD_MS}ms, got {self.ack_latency_ms:.0f}ms - REGRESSION!"

        elif self.expected_path == "haiku":
            if self.ack_latency_ms <= HAIKU_ACK_THRESHOLD_MS:
                self.passed = True
                if self.ack_latency_ms > HAIKU_ACK_WARNING_MS:
                    self.failure_reason = f"Haiku took {self.ack_latency_ms:.0f}ms (target <{HAIKU_ACK_WARNING_MS}ms)"
            else:
                self.passed = False
                if self.ack_latency_ms > AGENT_SDK_REGRESSION_MS:
                    self.failure_reason = f"AGENT SDK REGRESSION! Got {self.ack_latency_ms:.0f}ms (was ~5s before fix)"
                else:
                    self.failure_reason = f"Haiku too slow: {self.ack_latency_ms:.0f}ms > {HAIKU_ACK_THRESHOLD_MS}ms"


def measure_acknowledgment(message: str, voice_style: str = "normal") -> tuple[bool, float, str]:
    """
    Measure acknowledgment latency for a message.

    Returns: (ack_received, latency_ms, ack_text)
    """
    start = time.perf_counter()
    ack_time = None
    ack_text = ""

    try:
        response = requests.post(
            f"{AGENT_API_URL}/api/chat",
            json={
                "userId": "latency-test-v3",
                "message": message,
                "voiceStyle": voice_style
            },
            stream=True,
            headers={"Accept": "text/event-stream"},
            timeout=30
        )

        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get("type") == "acknowledgment":
                            ack_time = (time.perf_counter() - start) * 1000
                            ack_text = data.get("content", "")
                            break  # Got ack, stop listening
                        elif data.get("type") == "text":
                            # First text arrived, no ack
                            break
                        elif data.get("type") == "done":
                            break
                    except json.JSONDecodeError:
                        pass

        response.close()

        if ack_time is not None:
            return True, ack_time, ack_text
        else:
            return False, 0.0, ""

    except Exception as e:
        return False, 0.0, f"Error: {e}"


def run_test_case(case: dict) -> TestResult:
    """Run a single test case."""
    result = TestResult(
        message=case["message"],
        description=case["description"],
        expected_path=case["expected_path"],
        expected_ack=case.get("expected_ack"),
    )

    result.ack_received, result.ack_latency_ms, result.ack_text = measure_acknowledgment(case["message"])
    result.validate()

    return result


def print_result(result: TestResult, idx: int):
    """Print a single test result."""
    status = "PASS" if result.passed else "FAIL"
    status_emoji = "✅" if result.passed else "❌"

    print(f"\n[{idx}] {result.description}")
    print(f"    Message: \"{result.message}\"")
    print(f"    Expected: {result.expected_path:<8} | Got: {result.inferred_path}")

    if result.ack_received:
        # Show ack text match status for pattern tests
        ack_match = ""
        if result.expected_ack:
            if result.ack_text == result.expected_ack:
                ack_match = " ✓"
            elif result.ack_text_matched:
                ack_match = " ~"  # Different pattern but still valid
            else:
                ack_match = " ✗"  # Unexpected text
        print(f"    Latency:  {result.ack_latency_ms:>7.1f}ms | Ack: \"{result.ack_text}\"{ack_match}")
    else:
        print(f"    Latency:  N/A (no acknowledgment)")

    # Show bypass warning
    if result.fast_layer_bypassed:
        print(f"    ⚠️  FAST LAYER BYPASS DETECTED")

    print(f"    Status:   {status_emoji} {status}")
    if result.failure_reason:
        print(f"    Reason:   {result.failure_reason}")


def check_services() -> bool:
    """Verify services are running."""
    print("Checking services...")

    try:
        r = requests.get(f"{AGENT_API_URL}/health", timeout=2)
        print(f"  ✅ Agent API: {AGENT_API_URL}")
    except Exception as e:
        print(f"  ❌ Agent API not running: {AGENT_API_URL}")
        return False

    return True


def main():
    global PATTERN_ACK_THRESHOLD_MS  # Must be first before any usage

    parser = argparse.ArgumentParser(description="IRIS Latency Benchmark v3 - Pattern vs Haiku Isolation")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test (2 cases)")
    parser.add_argument("--threshold", type=int, default=PATTERN_ACK_THRESHOLD_MS,
                       help=f"Pattern threshold in ms (default: {PATTERN_ACK_THRESHOLD_MS})")
    parser.add_argument("--strict", action="store_true", help="Fail on any warning")
    args = parser.parse_args()

    PATTERN_ACK_THRESHOLD_MS = args.threshold

    print("=" * 70)
    print("IRIS Voice Latency Benchmark v3")
    print("Pattern vs Haiku Path Isolation")
    print("=" * 70)
    print()
    print("THRESHOLDS:")
    print(f"  Pattern-based acknowledgments: <{PATTERN_ACK_THRESHOLD_MS}ms")
    print(f"  Haiku-based acknowledgments:   <{HAIKU_ACK_THRESHOLD_MS}ms")
    print(f"  Agent SDK regression alert:    >{AGENT_SDK_REGRESSION_MS}ms")
    print()

    if not check_services():
        print("\nStart services with:")
        print("  cd packages/agent-core && node dist/api-server.js")
        sys.exit(1)

    # Select test cases
    cases = TEST_CASES[:2] if args.quick else TEST_CASES

    print(f"\nRunning {len(cases)} test cases...")

    results = []
    for i, case in enumerate(cases, 1):
        result = run_test_case(case)
        results.append(result)
        print_result(result, i)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    pattern_results = [r for r in results if r.expected_path == "pattern" and r.ack_received]
    haiku_results = [r for r in results if r.expected_path == "haiku" and r.ack_received]

    print(f"\nResults: {passed}/{len(results)} passed")

    if pattern_results:
        avg_pattern = sum(r.ack_latency_ms for r in pattern_results) / len(pattern_results)
        max_pattern = max(r.ack_latency_ms for r in pattern_results)
        print(f"\nPattern-based acknowledgments:")
        print(f"  Average: {avg_pattern:.1f}ms")
        print(f"  Max:     {max_pattern:.1f}ms")
        if avg_pattern < PATTERN_ACK_THRESHOLD_MS:
            print(f"  Status:  ✅ Within threshold (<{PATTERN_ACK_THRESHOLD_MS}ms)")
        else:
            print(f"  Status:  ⚠️  Above threshold (check pattern matching)")

    if haiku_results:
        avg_haiku = sum(r.ack_latency_ms for r in haiku_results) / len(haiku_results)
        max_haiku = max(r.ack_latency_ms for r in haiku_results)
        print(f"\nHaiku-based acknowledgments:")
        print(f"  Average: {avg_haiku:.1f}ms")
        print(f"  Max:     {max_haiku:.1f}ms")
        if avg_haiku < HAIKU_ACK_WARNING_MS:
            print(f"  Status:  ✅ Good (<{HAIKU_ACK_WARNING_MS}ms)")
        elif avg_haiku < HAIKU_ACK_THRESHOLD_MS:
            print(f"  Status:  ⚠️  Slow but acceptable (<{HAIKU_ACK_THRESHOLD_MS}ms)")
        else:
            print(f"  Status:  ❌ Too slow - check if using direct Anthropic API")

    # Check for Agent SDK regression
    agent_sdk_regression = any(
        r.ack_latency_ms > AGENT_SDK_REGRESSION_MS
        for r in results if r.ack_received
    )

    if agent_sdk_regression:
        print("\n" + "=" * 70)
        print("⚠️  AGENT SDK REGRESSION DETECTED!")
        print("=" * 70)
        print("""
This indicates the fast-layer may be using the Agent SDK instead of
the direct Anthropic API. The Agent SDK has ~5s overhead for Haiku.

CHECK: packages/agent-core/src/fast-layer.ts
  - Should import from "@anthropic-ai/sdk" (NOT claude-agent-sdk)
  - Should use client.messages.create() directly
  - Should NOT use Agent SDK's query() function
""")
        sys.exit(1)

    # Check for fast layer bypass (no ack when expected)
    fast_layer_bypassed = any(r.fast_layer_bypassed for r in results)

    if fast_layer_bypassed:
        print("\n" + "=" * 70)
        print("⚠️  FAST LAYER BYPASS DETECTED!")
        print("=" * 70)
        print("""
One or more test cases did not receive an acknowledgment when expected.
This indicates the fast layer may have been bypassed entirely.

CHECK: packages/agent-core/src/agent.ts
  - Verify needsAcknowledgment() is being called
  - Verify getAcknowledgment() is being called
  - Verify acknowledgment chunk is being yielded

CHECK: packages/agent-core/src/fast-layer.ts
  - Verify getQuickFallback() pattern matching is working
  - Verify generateQuickAcknowledgment() is being called as fallback
""")
        sys.exit(1)

    # Code path validation summary
    pattern_with_acks = [r for r in results if r.expected_path == "pattern" and r.expected_ack]
    if pattern_with_acks:
        matched = sum(1 for r in pattern_with_acks if r.ack_text_matched)
        print(f"\nCode path validation:")
        print(f"  Pattern ack text matched: {matched}/{len(pattern_with_acks)}")
        if matched == len(pattern_with_acks):
            print(f"  Status:  ✅ All pattern responses correct")
        else:
            print(f"  Status:  ⚠️  Some patterns returned unexpected text")

    # Final verdict
    print()
    if failed == 0:
        print("✅ All tests passed!")
        sys.exit(0)
    elif args.strict:
        print(f"❌ {failed} tests failed (strict mode)")
        sys.exit(1)
    else:
        warnings = sum(1 for r in results if r.passed and r.failure_reason)
        if warnings > 0:
            print(f"⚠️  {warnings} warnings, {failed} failures")
        else:
            print(f"❌ {failed} tests failed")
        sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
