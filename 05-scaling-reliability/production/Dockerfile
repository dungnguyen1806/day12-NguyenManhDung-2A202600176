FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY 05-scaling-reliability/production/app.py .
# Create a temporary requirements file or copy from develop if appropriate
# Looking at the code, it needs fastapi, uvicorn, redis, pydantic
RUN echo "fastapi\nuvicorn\nredis\npydantic" > requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runtime

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY 05-scaling-reliability/production/app.py .
COPY 05-scaling-reliability/production/utils /app/utils

RUN chown -R appuser:appuser /app

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
