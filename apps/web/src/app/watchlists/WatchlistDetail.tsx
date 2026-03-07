import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../../../api";
import type { Watchlist as W, Entity } from "../../../types";

export default function WatchlistDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState<W | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [entityIds, setEntityIds] = useState<number[]>([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.watchlists
      .get(Number(id))
      .then((w) => {
        setWatchlist(w);
        setName(w.name);
        setEntityIds(w.entity_ids);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    api.entities.list().then(setEntities).catch(() => {});
  }, []);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setError(null);
    try {
      const w = await api.watchlists.update(Number(id), { name, entity_ids: entityIds });
      setWatchlist(w);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update");
    }
  };

  const runNow = async () => {
    if (!id) return;
    setRunning(true);
    setError(null);
    try {
      const run = await api.runs.create(Number(id), "manual");
      navigate(`/runs/${run.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start run");
    } finally {
      setRunning(false);
    }
  };

  if (loading || !watchlist) return <p>{loading ? "Loading..." : "Not found"}</p>;
  const selectedEntities = entities.filter((e) => entityIds.includes(e.id));

  return (
    <div>
      <div className="page-header">
        <h1>{watchlist.name}</h1>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" onClick={runNow} disabled={running || watchlist.entity_ids.length === 0}>
            {running ? "Starting…" : "Run now"}
          </button>
          <button type="button" onClick={() => setEditing(!editing)}>
            {editing ? "Cancel" : "Edit"}
          </button>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {editing ? (
        <form onSubmit={save}>
          <div className="form-group">
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Entities</label>
            <select
              multiple
              value={entityIds.map(String)}
              onChange={(e) =>
                setEntityIds(Array.from(e.target.selectedOptions, (o) => Number(o.value)))
              }
            >
              {entities.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
          </div>
          <button type="submit">Save</button>
        </form>
      ) : (
        <>
          <p><strong>Entities:</strong> {selectedEntities.map((e) => e.name).join(", ") || "None"}</p>
          <p>
            <Link to={`/runs?watchlist_id=${id}`}>View runs for this watchlist</Link>
          </p>
        </>
      )}
    </div>
  );
}
