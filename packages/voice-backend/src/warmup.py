"""
Comprehensive warmup for all voice pipeline components.

Ensures first user interaction has minimal latency by pre-warming:
- STT: Run actual transcription on synthetic audio
- TTS: Synthesize test phrases
- LLM: Send warmup request to Ollama (if available)

Usage:
    from warmup import WarmupManager, get_warmup_manager

    # Option 1: Use singleton with environment defaults
    warmup = get_warmup_manager()
    await warmup.warmup_all()

    # Option 2: Create custom instance
    warmup = WarmupManager(ollama_model="mistral:7b")
    await warmup.warmup_all()

    if warmup.is_ready:
        # Safe to handle user requests
        pass

    # Switch to different LLM model at runtime
    await warmup.warmup_llm("llama3:8b")

    # Or set model without immediate warmup
    warmup.set_llm_model("phi3:mini")
    # ... later ...
    await warmup.warmup_llm()

Environment Variables (all optional, with defaults):
    OLLAMA_URL: Ollama API URL (default: http://localhost:11434)
    OLLAMA_MODEL: Default LLM model (default: qwen2.5:7b)
    STT_DEVICE: STT device - cpu, cuda, auto (default: cuda)
    TTS_DEVICE: TTS device - cpu, cuda, auto (default: cuda)
    STT_MODEL_SIZE: Whisper model size (default: base)

Command Line Testing:
    # Use default model from OLLAMA_MODEL env var
    python test_warmup.py

    # Specify model directly
    python test_warmup.py --model mistral:7b

    # Use CPU
    python test_warmup.py --cpu --model phi3:mini
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import requests

logger = logging.getLogger(__name__)

# Environment-based defaults (single source of truth)
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
DEFAULT_STT_DEVICE = os.getenv("STT_DEVICE", "cuda")
DEFAULT_TTS_DEVICE = os.getenv("TTS_DEVICE", "cuda")
DEFAULT_STT_MODEL_SIZE = os.getenv("STT_MODEL_SIZE", "base")


@dataclass
class WarmupStatus:
    """Status of each component's warmup."""
    stt_ready: bool = False
    stt_latency_ms: float = 0
    tts_ready: bool = False
    tts_latency_ms: float = 0
    llm_ready: bool = False
    llm_latency_ms: float = 0
    llm_model: str = ""
    total_time_ms: float = 0

    @property
    def is_ready(self) -> bool:
        """All critical components ready (LLM is optional)."""
        return self.stt_ready and self.tts_ready


class WarmupManager:
    """Manages warmup of all voice pipeline components."""

    def __init__(
        self,
        stt_device: Literal["cpu", "cuda", "auto"] | None = None,
        tts_device: Literal["cpu", "cuda", "auto"] | None = None,
        stt_model_size: str | None = None,
        ollama_url: str | None = None,
        ollama_model: str | None = None,
    ):
        # Use environment defaults if not specified
        self.stt_device = stt_device or DEFAULT_STT_DEVICE
        self.tts_device = tts_device or DEFAULT_TTS_DEVICE
        self.stt_model_size = stt_model_size or DEFAULT_STT_MODEL_SIZE
        self.ollama_url = ollama_url or DEFAULT_OLLAMA_URL
        self.ollama_model = ollama_model or DEFAULT_OLLAMA_MODEL
        self.status = WarmupStatus()
        self._warmup_complete = asyncio.Event()

    @property
    def is_ready(self) -> bool:
        """Check if warmup is complete."""
        return self.status.is_ready

    async def wait_until_ready(self, timeout: float = 60.0):
        """Wait until warmup is complete."""
        try:
            await asyncio.wait_for(self._warmup_complete.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Warmup timeout after {timeout}s")

    async def warmup_all(self) -> WarmupStatus:
        """
        Warm up all components in parallel where possible.

        Returns WarmupStatus with timing information.
        """
        total_start = time.perf_counter()
        logger.info("=" * 60)
        logger.info("WARMUP: Starting comprehensive warmup...")
        logger.info("=" * 60)

        # Run warmups concurrently
        await asyncio.gather(
            self._warmup_stt(),
            self._warmup_tts(),
            self._warmup_llm(),
            return_exceptions=True,
        )

        self.status.total_time_ms = (time.perf_counter() - total_start) * 1000

        # Log summary
        logger.info("=" * 60)
        logger.info("WARMUP COMPLETE")
        logger.info(f"  STT: {'✓' if self.status.stt_ready else '✗'} ({self.status.stt_latency_ms:.0f}ms)")
        logger.info(f"  TTS: {'✓' if self.status.tts_ready else '✗'} ({self.status.tts_latency_ms:.0f}ms)")
        logger.info(f"  LLM: {'✓' if self.status.llm_ready else '✗'} ({self.status.llm_latency_ms:.0f}ms) [{self.status.llm_model}]")
        logger.info(f"  Total: {self.status.total_time_ms:.0f}ms")
        logger.info("=" * 60)

        self._warmup_complete.set()
        return self.status

    async def _warmup_stt(self):
        """Warm up STT by running actual transcription."""
        try:
            logger.info("[STT] Loading model...")

            # Import here to avoid circular imports
            try:
                from .stt import get_stt
            except ImportError:
                from stt import get_stt

            loop = asyncio.get_event_loop()

            def do_warmup():
                start = time.perf_counter()

                # Get STT instance (loads model)
                stt = get_stt(self.stt_model_size, self.stt_device)
                _ = stt.model  # Force load

                # Generate 2 seconds of synthetic audio (silence with slight noise)
                sample_rate = 16000
                duration = 2.0
                samples = int(sample_rate * duration)
                # Add slight noise to make it realistic
                audio = np.random.randn(samples).astype(np.float32) * 0.01

                # Run actual transcription
                logger.info("[STT] Running warmup transcription...")
                result = stt.transcribe(audio, beam_size=1)

                elapsed = (time.perf_counter() - start) * 1000
                logger.info(f"[STT] Warmup complete: {elapsed:.0f}ms")
                return elapsed

            self.status.stt_latency_ms = await loop.run_in_executor(None, do_warmup)
            self.status.stt_ready = True

        except Exception as e:
            logger.error(f"[STT] Warmup failed: {e}")
            self.status.stt_ready = False

    async def _warmup_tts(self):
        """Warm up TTS by synthesizing multiple phrases."""
        try:
            logger.info("[TTS] Loading model...")

            try:
                from .tts_kokoro import get_kokoro_tts
            except ImportError:
                from tts_kokoro import get_kokoro_tts

            loop = asyncio.get_event_loop()

            def do_warmup():
                start = time.perf_counter()

                # Get TTS instance (loads model)
                tts = get_kokoro_tts(self.tts_device)
                _ = tts.pipeline  # Force load

                # Synthesize multiple phrases to fully warm up
                warmup_phrases = [
                    "Ready.",
                    "Hello, I am IRIS.",
                    "The Calico I is departing.",  # Tests Roman numeral preprocessing
                ]

                logger.info("[TTS] Running warmup synthesis...")
                for phrase in warmup_phrases:
                    tts.synthesize(phrase)

                elapsed = (time.perf_counter() - start) * 1000
                logger.info(f"[TTS] Warmup complete: {elapsed:.0f}ms")
                return elapsed

            self.status.tts_latency_ms = await loop.run_in_executor(None, do_warmup)
            self.status.tts_ready = True

        except Exception as e:
            logger.error(f"[TTS] Warmup failed: {e}")
            self.status.tts_ready = False

    async def _warmup_llm(self):
        """Warm up Ollama LLM with a simple request."""
        try:
            logger.info(f"[LLM] Warming up {self.ollama_model}...")

            loop = asyncio.get_event_loop()

            def do_warmup():
                start = time.perf_counter()

                try:
                    # Check if Ollama is available
                    response = requests.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": self.ollama_model,
                            "prompt": "Hello",
                            "stream": False,
                            "options": {
                                "num_predict": 10,  # Very short response
                            },
                        },
                        timeout=30,
                    )

                    if response.status_code == 200:
                        elapsed = (time.perf_counter() - start) * 1000
                        logger.info(f"[LLM] Warmup complete: {elapsed:.0f}ms")
                        return elapsed, True
                    else:
                        logger.warning(f"[LLM] Ollama returned {response.status_code}")
                        return 0, False

                except requests.exceptions.ConnectionError:
                    logger.warning("[LLM] Ollama not available (connection refused)")
                    return 0, False
                except requests.exceptions.Timeout:
                    logger.warning("[LLM] Ollama warmup timeout")
                    return 0, False

            latency, success = await loop.run_in_executor(None, do_warmup)
            self.status.llm_latency_ms = latency
            self.status.llm_ready = success
            self.status.llm_model = self.ollama_model if success else "unavailable"

        except Exception as e:
            logger.error(f"[LLM] Warmup failed: {e}")
            self.status.llm_ready = False
            self.status.llm_model = "error"

    async def warmup_llm(self, model: str | None = None) -> bool:
        """
        Public method to warm up a specific LLM model.

        Useful for switching models at runtime without full system warmup.

        Args:
            model: Ollama model name (e.g., 'qwen2.5:7b', 'mistral:7b').
                   If None, uses the current configured model.

        Returns:
            True if warmup succeeded, False otherwise.
        """
        if model:
            self.ollama_model = model

        await self._warmup_llm()
        return self.status.llm_ready

    def set_llm_model(self, model: str):
        """
        Set the LLM model without warming up.

        Call warmup_llm() after this to warm up the new model.

        Args:
            model: Ollama model name (e.g., 'qwen2.5:7b', 'mistral:7b')
        """
        self.ollama_model = model
        self.status.llm_ready = False
        self.status.llm_model = ""
        self.status.llm_latency_ms = 0


# Singleton instance
_warmup_manager: WarmupManager | None = None


def get_warmup_manager(
    stt_device: Literal["cpu", "cuda", "auto"] | None = None,
    tts_device: Literal["cpu", "cuda", "auto"] | None = None,
    stt_model_size: str | None = None,
    ollama_model: str | None = None,
    ollama_url: str | None = None,
) -> WarmupManager:
    """
    Get or create the warmup manager singleton.

    All parameters default to environment variables if not specified:
    - STT_DEVICE (default: cuda)
    - TTS_DEVICE (default: cuda)
    - STT_MODEL_SIZE (default: base)
    - OLLAMA_MODEL (default: qwen2.5:7b)
    - OLLAMA_URL (default: http://localhost:11434)
    """
    global _warmup_manager
    if _warmup_manager is None:
        _warmup_manager = WarmupManager(
            stt_device=stt_device,
            tts_device=tts_device,
            stt_model_size=stt_model_size,
            ollama_model=ollama_model,
            ollama_url=ollama_url,
        )
    return _warmup_manager


def reset_warmup_manager():
    """Reset the warmup manager singleton. Useful for testing."""
    global _warmup_manager
    _warmup_manager = None
