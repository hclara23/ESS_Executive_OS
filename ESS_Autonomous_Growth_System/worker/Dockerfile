FROM python:3.12-slim

WORKDIR /app

COPY worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY worker ./worker

ENV PYTHONPATH=/app/api:/app/worker

WORKDIR /app/worker

CMD ["python", "main.py"]
