# Build frontend
FROM node:20-alpine AS frontend
WORKDIR /app/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web ./
ENV VITE_API_URL=/api
RUN npm run build

# Runtime: API + worker (same image; Railway runs two services with different start commands)
FROM python:3.11-slim
WORKDIR /app

COPY packages/shared ./packages/shared
COPY apps/api/requirements.txt apps/worker/requirements.txt ./
RUN pip install --no-cache-dir -e packages/shared && \
    pip install -r apps/api/requirements.txt && \
    pip install -r apps/worker/requirements.txt

COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
COPY --from=frontend /app/web/dist ./apps/api/static

ENV PORT=8000
EXPOSE 8000

# Default: run API. For the worker service, set start command to:
# cd /app/apps/worker && PYTHONPATH=/app/apps/worker:/app/packages/shared rq worker $REDIS_URL default
CMD ["sh", "-c", "cd /app/apps/api && PYTHONPATH=/app/packages/shared uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
