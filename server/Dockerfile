FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install build deps for any native wheels, then remove to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
  && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt requirements-dev.txt requirements-api.txt ./

RUN pip install --no-cache-dir -r requirements.txt || true
RUN if [ -f requirements-api.txt ]; then pip install --no-cache-dir -r requirements-api.txt; fi || true

# Copy application
COPY . .

ENV PORT=8080

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT}"]
