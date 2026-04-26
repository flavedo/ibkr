FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ibkr_show_worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

COPY ibkr_show_backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY ibkr_show_worker/worker /app/worker
COPY ibkr_show_backend/app /app/backend/app

FROM node:18-slim AS frontend

WORKDIR /app

COPY ibkr_show_frontend/package*.json ./
RUN npm install

COPY ibkr_show_frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/worker /app/worker
COPY --from=builder /app/backend /app/backend
COPY --from=frontend /app/dist /app/dist

RUN echo 'server { listen 80; root /app/dist; index index.html; location / { try_files $uri $uri/ /index.html; } location /api/ { proxy_pass http://localhost:8000; } }' > /etc/nginx/conf.d/default.conf

ENV PYTHONPATH=/app

EXPOSE 80 8000

CMD nginx & cd /app/backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000