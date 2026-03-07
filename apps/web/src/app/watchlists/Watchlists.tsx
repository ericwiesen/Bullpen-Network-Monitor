import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../../api";
import type { Watchlist } from "../../../types";

export default function Watchlists() {
  const [list, setList] = useState<Watchlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [entityIds, setEntityIds] = useState<number[]>([]);
  const [entities, setEntities] = useState<{ id: number; name: string }[]>([]);

  useEffect(() => {
    api.watchlists.list().then(setList).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    api.entities.list().then((es) => setEntities(es.map((e) => ({ id: e.id, name: e.name })))).catch(() => {});
  }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const w = await api.watchlists.create({ name, entity_ids: entityIds });
      setList((prev) => [w, ...prev]);
      setName("");
      setEntityIds([]);
      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create");
    }
  };

  if (loading) return <p>Loading...</p>;
  return (
    <div>
      <div className="page-header">
        <h1>Watchlists</h1>
        <button type="button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "New watchlist"}
        </button>
      </div>
      {showForm && (
        <form onSubmit={create} style={{ marginBottom: "1.5rem" }}>
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
            <small style={{ display: "block", marginTop: "0.25rem" }}>Ctrl/Cmd+click to select multiple</small>
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit">Create</button>
        </form>
      )}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Entities</th>
              <th>Updated</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {list.map((w) => (
              <tr key={w.id}>
                <td>
                  <Link to={`/watchlists/${w.id}`}>{w.name}</Link>
                </td>
                <td>{w.entity_ids.length}</td>
                <td>{new Date(w.updated_at).toLocaleDateString()}</td>
                <td>
                  <Link to={`/watchlists/${w.id}`}>Edit</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
