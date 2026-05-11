### Stage 1: Build Next.js frontend
FROM node:20-alpine AS frontend

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci

COPY web/ ./
RUN npm run build


### Stage 2: Python backend + compiled frontend
FROM python:3.12-slim

WORKDIR /app

# Install Node.js (needed by yt-dlp's JS runtime)
RUN apt-get update && apt-get install -y --no-install-recommends nodejs && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and install — leverage layer cache
COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --no-dev --frozen

# Copy application source
COPY app/ ./app/
COPY agents/ ./agents/
COPY models/ ./models/
COPY prompts/ ./prompts/
COPY tools/ ./tools/

# Copy compiled frontend from stage 1
COPY --from=frontend /app/web/out ./web/out

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
