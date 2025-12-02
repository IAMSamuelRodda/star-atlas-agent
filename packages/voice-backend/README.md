# IRIS Voice Backend

Python FastAPI service providing speech-to-text (STT) and text-to-speech (TTS) for IRIS.

## Components

- **STT**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - 4x faster than OpenAI Whisper
- **TTS**: [Chatterbox](https://github.com/resemble-ai/chatterbox) - Expressive TTS with emotion control

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Run server
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8001/health
```

### Transcribe Audio (STT)
```bash
curl -X POST http://localhost:8001/transcribe \
  -F "audio=@recording.wav"
```

### Synthesize Speech (TTS)
```bash
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello Commander!"}' \
  --output speech.wav
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `STT_MODEL_SIZE` | `base` | Whisper model: tiny, base, small, medium, large-v3 |
| `VOICE_DEVICE` | `auto` | Compute device: cpu, cuda, auto |
| `PRELOAD_MODELS` | `false` | Load models on startup (slower start, faster first request) |

## RAM Requirements

| Model | RAM (int8) |
|-------|------------|
| tiny | ~100MB |
| base | ~200MB |
| small | ~800MB |
| medium | ~2GB |

For VPS deployment, `base` model is recommended (balance of accuracy and memory).

## Docker

```bash
# Build
docker build -t iris-voice-backend .

# Run
docker run -p 8001:8001 \
  -e STT_MODEL_SIZE=base \
  -e VOICE_DEVICE=cpu \
  iris-voice-backend
```
