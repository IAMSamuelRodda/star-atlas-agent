# IRIS Voice Backend
# Multi-stage build for optimized image size

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
FROM base AS deps

# Install uv for fast package installation
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (without the project itself)
RUN uv pip install --system --no-cache-dir \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.32.0 \
    faster-whisper>=1.1.0 \
    chatterbox-tts>=0.2.0 \
    numpy>=1.26.0 \
    scipy>=1.14.0 \
    python-multipart>=0.0.12 \
    pydantic>=2.10.0

# Production image
FROM base AS production

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 iris && chown -R iris:iris /app
USER iris

# Environment configuration
ENV PYTHONPATH=/app
ENV STT_MODEL_SIZE=base
ENV VOICE_DEVICE=cpu
ENV PRELOAD_MODELS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Run the server
EXPOSE 8001
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
