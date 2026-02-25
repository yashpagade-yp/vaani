# ==============================================================
# Vaani Backend — Dockerfile
# ==============================================================
# Builds a lightweight Python container for the FastAPI backend.
#
# Build:  docker build -t vaani-backend .
# Run:    docker run --env-file .env -p 8000:8000 vaani-backend
# ==============================================================

# ── Stage: Final Image ────────────────────────────────────────
FROM python:3.12-slim

# Set environment variables for Python
# PYTHONDONTWRITEBYTECODE: Prevents .pyc files (smaller image)
# PYTHONUNBUFFERED: Ensures logs appear in real-time in Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# ── Install system dependencies ──────────────────────────────
# Some Python packages (like pipecat, aiohttp) need these to compile
# OpenCV (cv2) — required by pipecat's SmallWebRTCTransport — needs
# libxcb, libgl1, and libglib2.0 for image/video processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    libxcb1 \
    libx11-6 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies (cached layer) ───────────────
# Copy ONLY requirements.txt first — Docker caches this layer.
# If your code changes but dependencies don't, pip install is skipped!
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy application code ────────────────────────────────────
# This layer rebuilds only when your code changes
COPY . .

# ── Expose the port FastAPI runs on ──────────────────────────
EXPOSE 8000

# ── Start the server ─────────────────────────────────────────
# Using uvicorn to serve the FastAPI app
# --host 0.0.0.0 : Listen on all interfaces (required in Docker)
# --port 8000    : Match the EXPOSE port
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
