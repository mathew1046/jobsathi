FROM python:3.12-slim AS core
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY backend/app/requirements*.txt /app/app/
RUN pip install --no-cache-dir -r app/requirements-core.txt
COPY backend/app /app/app
RUN mkdir -p /app/app/database
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5).raise_for_status()"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# The default image preserves voice/LLM functionality. The core target is sufficient
# for catalog ingestion/search, durable sessions, and database integration tests.
FROM core AS full
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r app/requirements.txt
