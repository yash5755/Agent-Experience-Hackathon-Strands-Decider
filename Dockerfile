FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DECIDER_MODE=ugmdu
ENV DECIDER_URL=https://da25tnxy06gjk.cloudfront.net
ENV LLM_PROVIDER=ugmdu
ENV LLM_MODEL_ID=qwen3.5-4b
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn demo.server:app --host 0.0.0.0 --port ${PORT:-7860}"]
