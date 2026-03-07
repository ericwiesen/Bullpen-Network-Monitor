"""
Run RQ worker. Use from repo root:
  PYTHONPATH=apps/worker:packages/shared python -m apps.worker.worker
Or from apps/worker:
  PYTHONPATH=.:../../packages/shared rq worker redis://localhost:6379/0 default
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
for p in (os.path.join(ROOT, "packages", "shared"), os.path.join(ROOT, "apps", "worker")):
    if p not in sys.path:
        sys.path.insert(0, p)

from rq import Worker, Queue, Connection
import redis

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
conn = redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker([Queue("default", connection=conn)])
        worker.work()
