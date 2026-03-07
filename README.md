# Network Monitor

Simple app for non-technical users: add people and companies, click **Run**, and see recent news/content in the output window.

- **One service** on Railway + **Postgres** (no Redis, no worker).
- **One page**: text box to add, list of entities, Run button, output area.

## Deploy on Railway

1. Create a new project. Add **PostgreSQL**.
2. Add a service from this repo. Railway will use the Dockerfile.
3. In the service, add variable **DATABASE_URL** (from the Postgres plugin – link it or copy the URL).
4. Under **Networking**, generate a domain.
5. Deploy. Open the URL – you get the web UI. Tables are created on first start.

## Run locally

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/monitoring
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000. Use Postgres (e.g. `docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15`) or any Postgres URL.

## Adding real search

Right now **Run** returns mock results. To use a real news/search API, edit `main.py` → function `do_run()`: replace the mock loop with calls to your search API and create `Result` rows from the response.
