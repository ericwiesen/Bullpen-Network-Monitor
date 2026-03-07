import { useEffect, useState } from "react";
import { api } from "../../../api";
import type { Entity as E } from "../../../types";

export default function Entities() {
  const [list, setList] = useState<E[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState<"company" | "person">("company");
  const [aliases, setAliases] = useState("");

  const load = () => {
    api.entities.list().then(setList).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const aliasList = aliases
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await api.entities.create({
        name,
        type,
        aliases: aliasList.map((alias) => ({ alias })),
      });
      load();
      setName("");
      setAliases("");
      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create");
    }
  };

  const remove = async (id: number) => {
    if (!confirm("Delete this entity?")) return;
    try {
      await api.entities.delete(id);
      setList((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  };

  if (loading) return <p>Loading...</p>;
  return (
    <div>
      <div className="page-header">
        <h1>Entities</h1>
        <button type="button" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "New entity"}
        </button>
      </div>
      {showForm && (
        <form onSubmit={create} style={{ marginBottom: "1.5rem" }}>
          <div className="form-group">
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Type</label>
            <select value={type} onChange={(e) => setType(e.target.value as "company" | "person")}>
              <option value="company">Company</option>
              <option value="person">Person</option>
            </select>
          </div>
          <div className="form-group">
            <label>Aliases (comma-separated)</label>
            <input value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="Acme Corp, Acme" />
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
              <th>Type</th>
              <th>Aliases</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {list.map((e) => (
              <tr key={e.id}>
                <td>{e.name}</td>
                <td>{e.type}</td>
                <td>{e.aliases.join(", ") || "—"}</td>
                <td>
                  <button type="button" onClick={() => remove(e.id)} style={{ fontSize: "0.85rem" }}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
