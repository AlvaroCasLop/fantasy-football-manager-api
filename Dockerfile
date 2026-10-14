# Multi-stage Dockerfile for FastAPI + Railway
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final production stage
FROM python:3.12-slim as runner

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Copy installed packages from builder
COPY --from=builder /opt/venv /opt/venv

# Copy project code
COPY . .

# Expose port (Railway overrides this with $PORT dynamically)
EXPOSE 8000

# Run Alembic migrations automatically on startup, then launch Uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
