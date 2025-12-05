#!/usr/bin/env python3
"""
Test warmup sequence for all voice pipeline components.

Usage:
    python test_warmup.py
    python test_warmup.py --cpu           # Use CPU instead of GPU
    python test_warmup.py --model mistral:7b  # Use specific LLM model
    python test_warmup.py --model llama3:8b --cpu  # Combine options

Environment Variables:
    OLLAMA_MODEL: Default LLM model (default: qwen2.5:7b)
    OLLAMA_URL: Ollama API URL (default: http://localhost:11434)
    STT_DEVICE: STT device (default: cuda)
    TTS_DEVICE: TTS device (default: cuda)
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

from warmup import WarmupManager, DEFAULT_OLLAMA_MODEL


async def test_warmup(device: str = "cuda", model: str | None = None):
    model = model or DEFAULT_OLLAMA_MODEL

    print("=" * 60)
    print("WARMUP TEST")
    print("=" * 60)
    print(f"Device: {device}")
    print(f"LLM Model: {model}")
    print()

    warmup = WarmupManager(
        stt_device=device,
        tts_device=device,
        ollama_model=model,
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


async def test_model_switching(device: str = "cuda"):
    """Test runtime model switching."""
    print("\n" + "=" * 60)
    print("MODEL SWITCHING TEST")
    print("=" * 60)

    warmup = WarmupManager(
        stt_device=device,
        tts_device=device,
        ollama_model="qwen2.5:7b",
    )

    # Initial warmup
    print("\n[1] Initial warmup with qwen2.5:7b...")
    await warmup.warmup_all()
    print(f"    LLM Ready: {warmup.status.llm_ready} [{warmup.status.llm_model}]")

    # Switch to different model
    print("\n[2] Switching to mistral:7b...")
    success = await warmup.warmup_llm("mistral:7b")
    print(f"    LLM Ready: {success} [{warmup.status.llm_model}]")

    # Switch back
    print("\n[3] Switching back to qwen2.5:7b...")
    success = await warmup.warmup_llm("qwen2.5:7b")
    print(f"    LLM Ready: {success} [{warmup.status.llm_model}]")

    print("\n" + "=" * 60)
    print("MODEL SWITCHING TEST COMPLETE")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Test warmup sequence for voice pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_warmup.py                     # Default (cuda, qwen2.5:7b)
    python test_warmup.py --model mistral:7b  # Different LLM model
    python test_warmup.py --cpu               # CPU mode
    python test_warmup.py --switch-test       # Test model switching
        """
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Use CPU instead of GPU"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help=f"LLM model to use (default: {DEFAULT_OLLAMA_MODEL})"
    )
    parser.add_argument(
        "--switch-test",
        action="store_true",
        help="Run model switching test instead of standard warmup"
    )
    args = parser.parse_args()

    device = "cpu" if args.cpu else "cuda"

    if args.switch_test:
        asyncio.run(test_model_switching(device))
    else:
        asyncio.run(test_warmup(device, args.model))


if __name__ == "__main__":
    main()
