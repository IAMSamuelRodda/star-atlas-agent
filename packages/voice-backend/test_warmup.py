#!/usr/bin/env python3
"""
Test warmup sequence for all voice pipeline components.

Usage:
    python test_warmup.py
    python test_warmup.py --cpu  # Use CPU instead of GPU
"""

import argparse
import asyncio
import os
import sys

# Setup cuDNN before any other imports
def _setup_cudnn():
    try:
        import nvidia.cudnn
        cudnn_lib = os.path.join(os.path.dirname(nvidia.cudnn.__file__), "lib")
        if os.path.exists(cudnn_lib):
            import ctypes
            ctypes.CDLL(os.path.join(cudnn_lib, "libcudnn.so.9"), mode=ctypes.RTLD_GLOBAL)
    except:
        pass

_setup_cudnn()

sys.path.insert(0, 'src')

from warmup import WarmupManager


async def test_warmup(device: str = "cuda"):
    print("=" * 60)
    print("WARMUP TEST")
    print("=" * 60)
    print(f"Device: {device}")
    print()

    warmup = WarmupManager(
        stt_device=device,
        tts_device=device,
        ollama_model='qwen2.5:7b'
    )
    status = await warmup.warmup_all()

    print()
    print("=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    print(f"  Ready:      {status.is_ready}")
    print(f"  STT Ready:  {status.stt_ready} ({status.stt_latency_ms:.0f}ms)")
    print(f"  TTS Ready:  {status.tts_ready} ({status.tts_latency_ms:.0f}ms)")
    print(f"  LLM Ready:  {status.llm_ready} ({status.llm_latency_ms:.0f}ms) [{status.llm_model}]")
    print(f"  Total Time: {status.total_time_ms:.0f}ms")
    print("=" * 60)

    if status.is_ready:
        print("\n✓ System is ready for user interaction!")
    else:
        print("\n✗ WARNING: System not fully ready")

    return status


def main():
    parser = argparse.ArgumentParser(description="Test warmup sequence")
    parser.add_argument("--cpu", action="store_true", help="Use CPU instead of GPU")
    args = parser.parse_args()

    device = "cpu" if args.cpu else "cuda"
    asyncio.run(test_warmup(device))


if __name__ == "__main__":
    main()
