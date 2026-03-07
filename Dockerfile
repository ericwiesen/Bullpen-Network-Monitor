# Frontend
FROM node:20-alpine AS frontend
WORKDIR /app/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web ./
ENV VITE_API_URL=/api
RUN npm run build

# API + worker
FROM python:3.11-slim
WORKDIR /app

COPY shared ./shared
COPY apps/api/requirements.txt ./api-requirements.txt
COPY apps/worker/requirements.txt ./worker-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt -r worker-requirements.txt

COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
COPY --from=frontend /app/web/dist ./apps/api/static

ENV PORT=8000
ENV PYTHONPATH=/app:/app/apps/worker
EXPOSE 8000

# API service (default). Worker: set start command to:
# rq worker $REDIS_URL default
CMD ["sh", "-c", "cd /app/apps/api && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
