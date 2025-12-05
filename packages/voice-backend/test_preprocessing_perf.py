#!/usr/bin/env python3
"""
Performance test for TTS text preprocessing.

Tests preprocessing latency and TTS output with various edge cases:
- Roman numerals (ship names, movie sequels, dates)
- Pronoun I (normal sentences)
- Yoda-speak (inverted sentences)
- Proper nouns with inverted I

Usage:
    python test_preprocessing_perf.py
    python test_preprocessing_perf.py --play  # Play audio output
"""

import argparse
import os
import sys
import time
import subprocess
import tempfile

# Setup paths
sys.path.insert(0, 'src')

import numpy as np
import scipy.io.wavfile as wav


def play_audio(audio_data, sample_rate=24000):
    """Play audio using aplay."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, sample_rate, audio_data)
        subprocess.run(["aplay", "-q", f.name], check=True)
        os.unlink(f.name)


def main():
    parser = argparse.ArgumentParser(description="Text preprocessing performance test")
    parser.add_argument("--play", action="store_true", help="Play audio output")
    args = parser.parse_args()

    # Import after path setup
    from text_processing import preprocess_for_tts
    from tts_kokoro import KokoroTTS

    # Test cases with expected conversions
    test_cases = [
        # Roman numerals - should convert
        ("The Calico I is my favorite ship", "ship name"),
        ("Apollo I launched in 1967", "mission name"),
        ("Super Bowl LVIII was amazing", "event numeral"),
        ("Henry VIII ruled England", "royal numeral"),
        ("Episode IV: A New Hope", "movie sequel"),
        ("World War II changed everything", "historical"),

        # Pronoun I - should preserve
        ("I am your assistant", "normal pronoun"),
        ("Can I help you today?", "question"),
        ("I think we should proceed", "statement"),

        # Yoda-speak - should preserve pronoun
        ("Hungry I am", "yoda adjective"),
        ("Strong I have become", "yoda verb"),
        ("Ready I will be", "yoda modal"),

        # Inverted proper nouns - should preserve pronoun
        ("Emily I know not", "inverted name"),
        ("Adelaide I have seen", "inverted place"),
        ("London I love dearly", "inverted city"),

        # Edge cases
        ("The Mark V armor from Iron Man", "product name"),
        ("Mix the ingredients well", "word with roman chars"),
    ]

    print("=" * 70)
    print("TTS Text Preprocessing Performance Test")
    print("=" * 70)

    # Load TTS
    print("\nLoading Kokoro TTS (CPU for consistent timing)...")
    tts = KokoroTTS(device='cpu')
    _ = tts.pipeline  # Force load
    print("TTS ready.\n")

    # Warmup preprocessing
    for _ in range(10):
        preprocess_for_tts("Warmup text III")

    print(f"{'Type':<20} {'Preproc':<10} {'TTS':<10} {'Total':<10}")
    print("-" * 70)

    preproc_times = []
    tts_times = []
    results = []

    for text, case_type in test_cases:
        # Measure preprocessing
        start = time.perf_counter()
        processed = preprocess_for_tts(text)
        preproc_ms = (time.perf_counter() - start) * 1000
        preproc_times.append(preproc_ms)

        # Measure TTS
        start = time.perf_counter()
        result = tts.synthesize(processed)
        tts_ms = (time.perf_counter() - start) * 1000
        tts_times.append(tts_ms)

        total_ms = preproc_ms + tts_ms

        # Show if text changed
        changed = "→" if processed != text else "="

        print(f"{case_type:<20} {preproc_ms:>7.2f}ms {tts_ms:>7.0f}ms {total_ms:>7.0f}ms")

        if processed != text:
            print(f"  {changed} IN:  {text[:50]}")
            print(f"    OUT: {processed[:50]}")

        results.append((text, processed, result, case_type))

    print("-" * 70)
    print(f"{'AVERAGE':<20} {np.mean(preproc_times):>7.2f}ms {np.mean(tts_times):>7.0f}ms {np.mean(preproc_times) + np.mean(tts_times):>7.0f}ms")
    print(f"{'MAX':<20} {np.max(preproc_times):>7.2f}ms {np.max(tts_times):>7.0f}ms")
    print(f"{'MIN':<20} {np.min(preproc_times):>7.2f}ms {np.min(tts_times):>7.0f}ms")

    # Play audio if requested
    if args.play:
        print("\n" + "=" * 70)
        print("Playing audio samples...")
        print("=" * 70)

        for text, processed, result, case_type in results:
            print(f"\n[{case_type}] {processed[:60]}")
            audio_int16 = (result.audio.squeeze() * 32767).astype(np.int16)
            play_audio(audio_int16, result.sample_rate)
            time.sleep(0.3)

    print("\n✓ Performance test complete")


if __name__ == "__main__":
    main()
