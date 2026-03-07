# Monitoring Service

Internal service to monitor companies and people: collect recent news, press releases, and web content via watchlists and manual or scheduled runs.

## Architecture

- **API** (FastAPI): watchlists, entities, runs, documents.
- **Worker** (RQ): runs the ingestion pipeline (search → fetch → dedupe/score → persist).
- **Web** (Vite + React): dashboard to manage watchlists, entities, and view run results.
- **Postgres**: entities, watchlists, runs, documents.
- **Redis**: job queue for runs.

## Deploy on Railway (no local Docker needed)

You can run everything on [Railway](https://railway.app) (as with Deal Agent). No Docker on your machine required.

1. **Create a new project** and add two plugins: **PostgreSQL** and **Redis** (or use Upstash Redis and add `REDIS_URL` in variables).

2. **Add a first service** from this repo (GitHub connect or deploy from CLI):
   - Railway will detect the **Dockerfile** and build the image.
   - Add variables: `DATABASE_URL` and `REDIS_URL` (from the Postgres/Redis plugins; Railway often injects these when you link the plugins).
   - This service runs the **API + web UI** (default start command). Give it a public domain in Settings.

3. **Add a second service** (worker) from the **same repo**:
   - Same build (Dockerfile). In **Settings → Deploy**, set **Custom Start Command** to:
     ```bash
     rq worker $REDIS_URL default
     ```
   - Use the same `DATABASE_URL` and `REDIS_URL` as the API (or link the same Postgres/Redis).

4. **Run DB migrations once**: the API runs `init_db()` on startup, so tables are created automatically on first deploy.
   with `DATABASE_URL` set to your Railway Postgres URL. The API also runs `init_db()` on startup, so tables are created automatically on first deploy if the app starts successfully.

5. Open the API service URL: you get the **dashboard** (React app) and the **API** at `/api/...`. Manual and scheduled runs (e.g. `POST /api/runs/schedule`) are processed by the worker.

**Optional:** To run scheduled monitoring on a timer, use [Railway Cron](https://docs.railway.app/reference/cron-jobs), or an external cron that calls `POST https://your-app.up.railway.app/api/runs/schedule`.

---

## Quick start (local)

### 1. Start infrastructure (optional: use Docker, or install Postgres + Redis locally)

With Docker:

```bash
cd monitoring-service/infra && docker compose up -d && cd ../..
```

Without Docker (e.g. Homebrew): install and start Postgres and Redis, then set `DATABASE_URL` and `REDIS_URL` in your environment.

### 2. Install Python deps and init DB

From repo root:

```bash
pip install -r apps/api/requirements.txt
pip install -r apps/worker/requirements.txt
```

Set env (or use defaults):

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/monitoring
export REDIS_URL=redis://localhost:6379/0
```

Create tables (run once, from repo root):

```bash
PYTHONPATH=.:apps/api python -c "from app.database import init_db; init_db()"
```

### 3. Run API

From repo root:

```bash
PYTHONPATH=.:apps/api uvicorn app.main:app --reload --app-dir apps/api
```

### 4. Run worker

In another terminal, from repo root:

```bash
PYTHONPATH=.:apps/worker python -m rq worker redis://localhost:6379/0 default
```

### 5. Run web UI

```bash
cd apps/web && npm run dev
```

Open http://localhost:5173. API is at http://localhost:8000.

## Scheduled monitoring

To run all watchlists on a schedule (e.g. daily), call:

```bash
curl -X POST http://localhost:8000/runs/schedule
```

Use cron or a scheduler:

```cron
0 9 * * * curl -s -X POST http://localhost:8000/runs/schedule
```

## Search provider (MVP vs production)

By default the worker uses a **mock search** that returns placeholder results. To use a real search API, set:

- `SEARCH_API_URL` – endpoint that accepts `q` and `num` and returns `results` or `items` with `title`, `url`, `snippet`, `source`.
- `SEARCH_API_KEY` – auth header or query param as needed.

## Project layout

- `apps/api` – FastAPI app and routes (watchlists, entities, runs).
- `apps/worker` – RQ jobs: search, fetch, dedupe/score, run orchestration.
- `apps/web` – React dashboard (watchlists, entities, runs, results).
- `shared` – SQLAlchemy models and DB helpers (used by API and worker).
- `infra` – docker-compose (Postgres, Redis) for local dev only; on Railway, use Postgres + Redis plugins.
