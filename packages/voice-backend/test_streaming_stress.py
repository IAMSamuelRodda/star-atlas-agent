#!/usr/bin/env python3
"""
Streaming Stress Test - Extended LLM responses with chunked TTS.

Tests the full pipeline with longer LLM outputs:
1. LLM generates extended response (streaming)
2. Buffer sentences/phrases
3. TTS synthesizes each chunk
4. Audio plays progressively

This simulates real conversational AI where responses are spoken
as they're generated, not waiting for full completion.

Usage:
    python test_streaming_stress.py
    python test_streaming_stress.py --model qwen2.5:7b
    python test_streaming_stress.py --model mistral:7b --tokens 500
    python test_streaming_stress.py --no-play  # Don't play audio, just measure
"""

import os
import sys
import time
import json
import re
import uuid
import requests
import numpy as np
import scipy.io.wavfile as wav
import subprocess
import tempfile
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

# Setup cuDNN before imports
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

from tts_kokoro import get_kokoro_tts
from warmup import WarmupManager, DEFAULT_OLLAMA_MODEL

# Benchmark results directory
BENCHMARKS_DIR = Path(__file__).parent / "benchmarks" / "results"


def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
    except:
        return "unknown"


def get_gpu_info() -> str:
    """Get GPU information."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
        return "CPU only"
    except:
        return "unknown"


def save_benchmark_results(
    metrics_list: list,
    model: str,
    max_tokens: int,
    device: str,
    warmup_enabled: bool,
    audio_playback: bool,
    notes: str = "",
) -> str:
    """
    Save benchmark results to JSONL file.

    Returns the path to the saved file.
    """
    BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = BENCHMARKS_DIR / "streaming.jsonl"

    # Calculate aggregates
    avg_first_token = np.mean([m.time_to_first_token_ms for m in metrics_list])
    avg_first_audio = np.mean([m.time_to_first_audio_ms for m in metrics_list])
    avg_tokens_per_sec = np.mean([m.llm_tokens_per_sec for m in metrics_list])
    total_tokens = sum(m.total_tokens for m in metrics_list)
    total_chars = sum(m.total_chars for m in metrics_list)
    total_tts_chunks = sum(m.chunks_synthesized for m in metrics_list)
    total_tts_time = sum(m.total_tts_time_ms for m in metrics_list)
    total_audio_duration = sum(m.audio_duration_sec for m in metrics_list)

    # Build result record
    result = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_type": "streaming",
        "script": "test_streaming_stress.py",
        "git_commit": get_git_commit(),
        "architecture": {
            "stt": {
                "engine": "faster-whisper",
                "model": "base",
                "device": device,
            },
            "tts": {
                "engine": "kokoro",
                "model": "Kokoro-82M",
                "device": device,
                "voice": "af_heart",
            },
            "llm": {
                "provider": "ollama",
                "model": model,
                "endpoint": "http://localhost:11434",
                "options": {"num_predict": max_tokens},
            },
            "hardware": {
                "gpu": get_gpu_info(),
            },
        },
        "parameters": {
            "model": model,
            "max_tokens": max_tokens,
            "num_prompts": len(metrics_list),
            "prompt_type": "stress_test",
            "warmup_enabled": warmup_enabled,
            "audio_playback": audio_playback,
        },
        "results": {
            "first_token_ms": round(avg_first_token, 2),
            "first_audio_ms": round(avg_first_audio, 2),
            "tokens_per_sec": round(avg_tokens_per_sec, 2),
            "total_tokens": total_tokens,
            "total_chars": total_chars,
            "tts_chunks": total_tts_chunks,
            "tts_time_ms": round(total_tts_time, 2),
            "audio_duration_sec": round(total_audio_duration, 2),
        },
        "per_run_results": [
            {
                "prompt": m.prompt,
                "first_token_ms": round(m.time_to_first_token_ms, 2),
                "first_audio_ms": round(m.time_to_first_audio_ms, 2),
                "total_time_ms": round(m.total_time_ms, 2),
                "tokens": m.total_tokens,
                "tts_chunks": m.chunks_synthesized,
            }
            for m in metrics_list
        ],
        "notes": notes,
    }

    # Append to JSONL file
    with open(results_file, "a") as f:
        f.write(json.dumps(result) + "\n")

    print(f"\nResults saved to: {results_file}")
    return str(results_file)


@dataclass
class StreamingMetrics:
    """Metrics from a streaming test."""
    prompt: str
    model: str
    total_tokens: int
    total_chars: int
    chunks_synthesized: int
    time_to_first_token_ms: float
    time_to_first_audio_ms: float
    total_llm_time_ms: float
    total_tts_time_ms: float
    total_time_ms: float
    llm_tokens_per_sec: float
    audio_duration_sec: float


# Prompts designed to elicit longer responses
STRESS_PROMPTS = [
    "Tell me a short story about a space captain discovering an ancient alien artifact. Include dialogue.",
    "Explain the process of stellar fusion in detail, as if teaching a curious student.",
    "Describe your ideal day as an AI assistant, moment by moment, with feelings and observations.",
    "Write a dramatic monologue from the perspective of a ship's AI warning its crew of danger.",
    "List and explain five tips for new Star Atlas players, with specific examples for each.",
]

# System prompt for extended responses
SYSTEM_PROMPT = """You are IRIS, an eloquent AI assistant for Star Atlas players.
For this test, provide detailed, flowing responses suitable for text-to-speech.
Use natural speech patterns. Avoid markdown, bullets, or special formatting.
Speak as if narrating or having a conversation."""


def play_audio(audio_data, sample_rate=24000):
    """Play audio using aplay."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, sample_rate, audio_data)
        subprocess.run(["aplay", "-q", f.name], check=True)
        os.unlink(f.name)


def stream_ollama(model: str, prompt: str, max_tokens: int = 500) -> Generator[str, None, dict]:
    """
    Stream tokens from Ollama.

    Yields individual tokens as they arrive.
    Returns final stats dict when complete.
    """
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
            },
        },
        stream=True,
        timeout=120,
    )

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.status_code}")

    total_tokens = 0
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            token = data.get("response", "")
            if token:
                total_tokens += 1
                yield token

            if data.get("done"):
                return {
                    "total_tokens": total_tokens,
                    "eval_count": data.get("eval_count", total_tokens),
                    "eval_duration": data.get("eval_duration", 0),
                }


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences for chunked TTS."""
    # Split on sentence-ending punctuation followed by space or end
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def run_streaming_test(
    tts,
    prompt: str,
    model: str,
    max_tokens: int = 500,
    play_audio_flag: bool = True,
) -> StreamingMetrics:
    """
    Run a single streaming stress test.

    Streams LLM output, buffers sentences, synthesizes and plays progressively.
    """
    print(f"\n{'='*70}")
    print(f"STREAMING TEST: {model}")
    print(f"{'='*70}")
    print(f"Prompt: {prompt[:60]}...")
    print(f"Max tokens: {max_tokens}")
    print()

    # Metrics tracking
    start_time = time.perf_counter()
    time_to_first_token = None
    time_to_first_audio = None
    total_tts_time = 0
    chunks_synthesized = 0
    total_audio_duration = 0

    # Buffer for accumulating tokens into sentences
    token_buffer = ""
    full_response = ""
    total_tokens = 0

    print("[LLM] Streaming response...")
    llm_start = time.perf_counter()

    try:
        streamer = stream_ollama(model, prompt, max_tokens)

        while True:
            try:
                token = next(streamer)
                total_tokens += 1

                # Track time to first token
                if time_to_first_token is None:
                    time_to_first_token = (time.perf_counter() - start_time) * 1000
                    print(f"      First token: {time_to_first_token:.0f}ms")

                token_buffer += token
                full_response += token

                # Print tokens as they arrive (on same line)
                print(token, end="", flush=True)

                # Check if we have complete sentences to synthesize
                sentences = split_into_sentences(token_buffer)

                # If we have at least one complete sentence and more content after it
                if len(sentences) > 1:
                    # Synthesize all complete sentences (keep last partial one)
                    to_synthesize = " ".join(sentences[:-1])
                    token_buffer = sentences[-1]

                    # TTS synthesis
                    tts_start = time.perf_counter()
                    result = tts.synthesize(to_synthesize)
                    tts_time = (time.perf_counter() - tts_start) * 1000
                    total_tts_time += tts_time
                    chunks_synthesized += 1
                    total_audio_duration += result.duration_seconds

                    # Track time to first audio
                    if time_to_first_audio is None:
                        time_to_first_audio = (time.perf_counter() - start_time) * 1000

                    print(f"\n      [TTS #{chunks_synthesized}] {tts_time:.0f}ms | {result.duration_seconds:.1f}s audio")

                    # Play audio
                    if play_audio_flag:
                        audio_int16 = (result.audio.squeeze() * 32767).astype(np.int16)
                        play_audio(audio_int16, result.sample_rate)

            except StopIteration:
                break

        llm_time = (time.perf_counter() - llm_start) * 1000

    except Exception as e:
        print(f"\nError during streaming: {e}")
        raise

    # Synthesize any remaining buffer
    if token_buffer.strip():
        print(f"\n      [TTS final] Synthesizing remaining: {token_buffer[:40]}...")
        tts_start = time.perf_counter()
        result = tts.synthesize(token_buffer)
        tts_time = (time.perf_counter() - tts_start) * 1000
        total_tts_time += tts_time
        chunks_synthesized += 1
        total_audio_duration += result.duration_seconds

        if time_to_first_audio is None:
            time_to_first_audio = (time.perf_counter() - start_time) * 1000

        print(f"      [TTS #{chunks_synthesized}] {tts_time:.0f}ms | {result.duration_seconds:.1f}s audio")

        if play_audio_flag:
            audio_int16 = (result.audio.squeeze() * 32767).astype(np.int16)
            play_audio(audio_int16, result.sample_rate)

    total_time = (time.perf_counter() - start_time) * 1000

    # Calculate tokens per second
    tokens_per_sec = (total_tokens / (llm_time / 1000)) if llm_time > 0 else 0

    metrics = StreamingMetrics(
        prompt=prompt[:50],
        model=model,
        total_tokens=total_tokens,
        total_chars=len(full_response),
        chunks_synthesized=chunks_synthesized,
        time_to_first_token_ms=time_to_first_token or 0,
        time_to_first_audio_ms=time_to_first_audio or 0,
        total_llm_time_ms=llm_time,
        total_tts_time_ms=total_tts_time,
        total_time_ms=total_time,
        llm_tokens_per_sec=tokens_per_sec,
        audio_duration_sec=total_audio_duration,
    )

    # Print summary
    print(f"\n{'-'*70}")
    print(f"METRICS:")
    print(f"  Tokens:          {metrics.total_tokens} ({metrics.total_chars} chars)")
    print(f"  TTS chunks:      {metrics.chunks_synthesized}")
    print(f"  First token:     {metrics.time_to_first_token_ms:.0f}ms")
    print(f"  First audio:     {metrics.time_to_first_audio_ms:.0f}ms")
    print(f"  LLM time:        {metrics.total_llm_time_ms:.0f}ms ({metrics.llm_tokens_per_sec:.1f} tok/s)")
    print(f"  TTS time:        {metrics.total_tts_time_ms:.0f}ms")
    print(f"  Audio duration:  {metrics.audio_duration_sec:.1f}s")
    print(f"  Total time:      {metrics.total_time_ms:.0f}ms")
    print(f"{'-'*70}")

    return metrics


async def warmup_system(device: str, model: str):
    """Warm up all components before stress testing."""
    print("="*70)
    print("WARMUP PHASE")
    print("="*70)

    warmup = WarmupManager(
        stt_device=device,
        tts_device=device,
        ollama_model=model,
    )
    status = await warmup.warmup_all()

    if not status.is_ready:
        print("WARNING: Not all components ready!")

    return status


def main():
    parser = argparse.ArgumentParser(
        description="Streaming stress test for voice pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_OLLAMA_MODEL,
        help=f"LLM model (default: {DEFAULT_OLLAMA_MODEL})"
    )
    parser.add_argument(
        "--tokens", "-t",
        type=int,
        default=300,
        help="Max tokens per response (default: 300)"
    )
    parser.add_argument(
        "--prompts", "-p",
        type=int,
        default=3,
        help="Number of prompts to test (default: 3)"
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Don't play audio, just measure latencies"
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Use CPU instead of GPU"
    )
    parser.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Skip warmup phase"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save results to benchmarks/results/streaming.jsonl"
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Notes to include with saved results"
    )
    args = parser.parse_args()

    device = "cpu" if args.cpu else "cuda"
    play_audio_flag = not args.no_play

    print("="*70)
    print("STREAMING STRESS TEST")
    print("="*70)
    print(f"Model:      {args.model}")
    print(f"Max tokens: {args.tokens}")
    print(f"Prompts:    {args.prompts}")
    print(f"Device:     {device}")
    print(f"Play audio: {play_audio_flag}")
    print()

    # Warmup
    if not args.skip_warmup:
        import asyncio
        asyncio.run(warmup_system(device, args.model))

    # Load TTS
    print("\nLoading TTS...")
    tts = get_kokoro_tts(device)
    _ = tts.pipeline  # Force load
    print("TTS ready!")

    # Run tests
    prompts_to_test = STRESS_PROMPTS[:args.prompts]
    all_metrics = []

    for i, prompt in enumerate(prompts_to_test, 1):
        print(f"\n\n{'#'*70}")
        print(f"# TEST {i}/{len(prompts_to_test)}")
        print(f"{'#'*70}")

        try:
            metrics = run_streaming_test(
                tts=tts,
                prompt=prompt,
                model=args.model,
                max_tokens=args.tokens,
                play_audio_flag=play_audio_flag,
            )
            all_metrics.append(metrics)
        except Exception as e:
            print(f"Test failed: {e}")

        time.sleep(1)  # Brief pause between tests

    # Final summary
    if all_metrics:
        print("\n\n" + "="*70)
        print("STRESS TEST SUMMARY")
        print("="*70)
        print(f"Model: {args.model}")
        print(f"Tests completed: {len(all_metrics)}/{len(prompts_to_test)}")
        print()

        avg_first_token = np.mean([m.time_to_first_token_ms for m in all_metrics])
        avg_first_audio = np.mean([m.time_to_first_audio_ms for m in all_metrics])
        avg_tokens_per_sec = np.mean([m.llm_tokens_per_sec for m in all_metrics])
        avg_tts_time = np.mean([m.total_tts_time_ms for m in all_metrics])
        total_audio = sum(m.audio_duration_sec for m in all_metrics)

        print(f"Avg time to first token:  {avg_first_token:.0f}ms")
        print(f"Avg time to first audio:  {avg_first_audio:.0f}ms")
        print(f"Avg LLM throughput:       {avg_tokens_per_sec:.1f} tokens/sec")
        print(f"Avg TTS time per test:    {avg_tts_time:.0f}ms")
        print(f"Total audio generated:    {total_audio:.1f}s")
        print()

        # Latency breakdown per test
        print("Per-test breakdown:")
        print(f"{'Prompt':<30} {'Tokens':>8} {'1st Tok':>10} {'1st Audio':>10} {'Total':>10}")
        print("-"*70)
        for m in all_metrics:
            print(f"{m.prompt:<30} {m.total_tokens:>8} {m.time_to_first_token_ms:>9.0f}ms {m.time_to_first_audio_ms:>9.0f}ms {m.total_time_ms:>9.0f}ms")

        print("="*70)

        # Save results if requested
        if args.save_results:
            save_benchmark_results(
                metrics_list=all_metrics,
                model=args.model,
                max_tokens=args.tokens,
                device=device,
                warmup_enabled=not args.skip_warmup,
                audio_playback=play_audio_flag,
                notes=args.notes,
            )


if __name__ == "__main__":
    main()
