FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libsndfile1 curl && rm -rf /var/lib/apt/lists/*

# Download Kokoro models during build to avoid massive source upload
RUN curl -L -o kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx && \
    curl -L -o voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY server ./server
COPY Features ./Features
COPY Data ./Data
COPY Brain ./Brain
COPY tools ./tools
COPY docs ./docs
COPY public ./public
COPY sitecustomize.py ./
COPY GEMINI.md ./
COPY README.md ./
COPY DEPLOYMENT.md ./
COPY SECURITY.md ./
COPY STATUS.md ./
COPY config.md ./

ENV ELIO_ENV=production
ENV ELIO_HEADLESS=true

CMD uvicorn server.app:app --host 0.0.0.0 --port $PORT
