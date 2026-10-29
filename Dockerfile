# Multi-stage Dockerfile for Real-Time People Counting & Crowd Density System
FROM python:3.11-slim as backend

WORKDIR /app

# Install system dependencies for OpenCV and multimedia
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate sample demonstration video
RUN python scripts/generate_sample_video.py

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
