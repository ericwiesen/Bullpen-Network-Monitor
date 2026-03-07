import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../../api";
import type { Run, Watchlist } from "../../../types";

export default function Runs() {
  const [searchParams] = useSearchParams();
  const watchlistId = searchParams.get("watchlist_id");
  const [runs, setRuns] = useState<Run[]>([]);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = watchlistId ? Number(watchlistId) : undefined;
    api.runs.list(id).then(setRuns).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [watchlistId]);

  useEffect(() => {
    api.watchlists.list().then(setWatchlists).catch(() => {});
  }, []);

  const watchlistMap = Object.fromEntries(watchlists.map((w) => [w.id, w.name]));

  if (loading) return <p>Loading...</p>;
  return (
    <div>
      <div className="page-header">
        <h1>Runs</h1>
      </div>
      {watchlists.length > 0 && (
        <p style={{ marginBottom: "1rem" }}>
          Filter:{" "}
          <Link to="/runs">All</Link>
          {watchlists.map((w) => (
            <span key={w.id}>
              {" | "}
              <Link to={`/runs?watchlist_id=${w.id}`}>{w.name}</Link>
            </span>
          ))}
        </p>
      )}
      {error && <div className="error">{error}</div>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Watchlist</th>
              <th>Trigger</th>
              <th>Status</th>
              <th>Started</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{watchlistMap[r.watchlist_id] ?? r.watchlist_id}</td>
                <td>{r.trigger}</td>
                <td>
                  <span className={`badge ${r.status}`}>{r.status}</span>
                </td>
                <td>{new Date(r.started_at).toLocaleString()}</td>
                <td>
                  <Link to={`/runs/${r.id}`}>View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
