# Voice Backend Benchmarks

> **Purpose**: Track performance metrics across different architectures and configurations
> **Updated**: After significant architecture changes or optimization work

---

## Data Storage

Benchmark results are stored in structured JSONL format for analysis and reporting:

```
benchmarks/
├── schema.json          # JSON Schema for result records
├── results/
│   └── streaming.jsonl  # Streaming stress test results
└── README.md            # Query examples
```

### Saving Results

```bash
# Run test and save results
python test_streaming_stress.py --model qwen2.5:7b --save-results

# Add notes for context
python test_streaming_stress.py --model mistral:7b --save-results --notes "After optimization X"
```

### Querying Results

```bash
# View latest result
tail -1 benchmarks/results/streaming.jsonl | python3 -m json.tool

# Get all results for a model
cat benchmarks/results/streaming.jsonl | jq 'select(.parameters.model == "qwen2.5:7b")'

# Compare models
cat benchmarks/results/streaming.jsonl | jq -s 'group_by(.parameters.model) | .[] | {model: .[0].parameters.model, avg_first_audio: ([.[].results.first_audio_ms] | add / length)}'
```

---

## Current Architecture (2025-12-05)

**Stack**: faster-whisper (STT) + Kokoro-82M (TTS) + Ollama (LLM)
**Hardware**: NVIDIA GPU (CUDA)
**Protocol**: Streaming LLM → sentence buffer → chunked TTS → progressive playback

---

## Benchmark Results

### Native Client (iris-local) - 2025-12-05

Test configuration:
- Script: `iris_local.py` (benchmark mode)
- Hardware: RTX 4090 (CUDA)
- Components: sounddevice → Silero VAD → faster-whisper → Ollama → Kokoro → sounddevice

#### First Audio Latency (warm, 3 queries)

| Query | LLM First Token | TTS First Chunk | First Audio |
|-------|-----------------|-----------------|-------------|
| "What is your name?" | 78ms | 40ms | **118ms** |
| "Give me a quick status update." | 78ms | 45ms | **123ms** |
| "Hello, how are you?" | 73ms | 23ms | **96ms** |

#### Comparison: iris-local vs Web Stack

| Architecture | First Audio | Overhead |
|--------------|-------------|----------|
| Web stack (WebSocket + base64) | 300-500ms | ~200ms network + encoding |
| **iris-local (direct audio)** | **96-123ms** | **None** |

**Improvement**: ~200-300ms latency reduction by eliminating web infrastructure.

---

### Streaming Stress Test (2025-12-05)

Test configuration:
- Script: `test_streaming_stress.py`
- Tokens: 300 (standard), 500 (extended)
- Prompts: Story generation, educational explanation
- Audio: Progressive playback via sentence chunking

#### Model Comparison (300 tokens, warm)

| Model | First Token | First Audio | Tokens/sec | TTS/chunk |
|-------|-------------|-------------|------------|-----------|
| qwen2.5:7b | 70-88ms | 180-434ms | 122 tok/s | 70-95ms |
| llama3.1:8b | 80-96ms | 288-480ms | 116 tok/s | 45-98ms |
| mistral:7b | 23ms | 138ms | 127 tok/s | 70-160ms |

#### Cold Start Penalty

| Model | Cold First Token | Warm First Token | Penalty |
|-------|------------------|------------------|---------|
| qwen2.5:7b | ~90ms | ~80ms | ~10ms |
| llama3.1:8b | ~1444ms | ~80ms | ~1360ms |
| mistral:7b | ~1202ms | ~23ms | ~1180ms |

**Note**: Cold start occurs when model isn't loaded in Ollama. Warmup eliminates this.

#### Extended Token Test (500 tokens, qwen2.5:7b)

| Metric | Test 1 (Story) | Test 2 (Education) |
|--------|----------------|-------------------|
| Tokens | 500 | 480 |
| Characters | 2300 | 2295 |
| TTS Chunks | 29 | 24 |
| First Token | 94ms | 70ms |
| First Audio | 1164ms | 181ms |
| Total TTS Time | 3468ms | 1948ms |
| Audio Duration | 156.2s | 156.7s |
| Total Time | 4378ms | 4026ms |

---

### Component Warmup Benchmarks (2025-12-05)

Test configuration:
- Script: `test_warmup.py`
- Device: CUDA

| Component | Cold Load | Warm Inference |
|-----------|-----------|----------------|
| STT (faster-whisper base) | ~990ms | 22-28ms |
| TTS (Kokoro-82M) | ~2997ms | 40-95ms |
| LLM (qwen2.5:7b) | ~1439ms | 70-90ms first token |

**Total warmup time**: ~3.8s (parallel execution)

---

### Text Preprocessing Benchmarks (2025-12-05)

Test configuration:
- Script: `test_preprocessing_perf.py`
- Function: `preprocess_for_tts()`

| Metric | Value |
|--------|-------|
| Avg time per call | 0.01-0.02ms |
| Test cases | 26 |
| Overhead | Negligible |

Features tested:
- Roman numeral conversion (I→one, II→two, etc.)
- Pronoun preservation ("I am", "Can I")
- Yoda-speak handling ("Hungry I am")
- CJK character handling

---

## Historical Benchmarks

### Pre-Streaming Architecture (2025-12-04)

Before implementing streaming LLM + chunked TTS:

| Metric | Value |
|--------|-------|
| STT (warm) | 22-28ms |
| TTS (warm) | 40-42ms |
| LLM (non-streaming) | 170-290ms (100 tokens) |
| Total round-trip | ~300-400ms |

**Limitation**: Full LLM response required before TTS could start.

---

## Performance Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| Voice round-trip | <500ms | ~300-480ms (web), **96-123ms (native)** |
| STT latency | <50ms | 22-28ms |
| TTS latency | <50ms | 40-95ms per chunk |
| Text preprocessing | <1ms | 0.01-0.02ms |
| First audio (streaming) | <500ms | 138-480ms (web), **96-123ms (native)** |
| First audio (native) | <150ms | **96-123ms** |

---

## Test Scripts

| Script | Purpose |
|--------|---------|
| `iris_local.py` | Native Python client (PTT/VAD modes) |
| `test_warmup.py` | Component warmup validation |
| `test_voice_flow.py` | Basic STT→LLM→TTS flow |
| `test_streaming_stress.py` | Extended streaming with metrics |
| `test_preprocessing_perf.py` | Text preprocessing performance |

---

## Notes

### Streaming Architecture Benefits

1. **Time to first audio**: User hears response within ~300-500ms
2. **Progressive delivery**: Natural pauses at sentence boundaries
3. **Scalability**: Handles 500+ token responses without timeout
4. **Memory efficient**: Processes chunks, not full responses

### Known Bottlenecks

1. **Cold model loading**: First request to un-warmed LLM adds 1-1.5s
2. **Audio playback**: Synchronous playback blocks next chunk (by design for testing)
3. **Sentence detection**: Simple regex may split mid-sentence on edge cases

### Future Optimization Opportunities

1. Async audio playback (parallel with LLM streaming)
2. Smaller TTS chunks for faster first audio
3. Multi-model warmup for quick switching
4. WebSocket streaming to browser (eliminate file I/O)

---

**Last Updated**: 2025-12-05
