FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ibkr_show_worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

COPY ibkr_show_backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

FROM node:18-slim AS frontend-builder

WORKDIR /app

COPY ibkr_show_frontend/package*.json ./
RUN rm -f package-lock.json && npm install

COPY ibkr_show_frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY ibkr_show_worker/ /app/worker/
COPY ibkr_show_backend/ /app/backend/
COPY --from=frontend-builder /app/dist /app/frontend/dist

ENV PYTHONPATH=/app
ENV PATH="/app/worker:/app/backend:${PATH}"

EXPOSE 8000 5173

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]