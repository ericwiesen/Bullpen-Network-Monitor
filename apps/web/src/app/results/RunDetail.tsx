import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../../../api";
import type { Run, Document } from "../../../types";

export default function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.runs
      .get(Number(id))
      .then(setRun)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    api.runs.documents(Number(id)).then(setDocuments).catch(() => {});
  }, [id]);

  if (loading || !run) return <p>{loading ? "Loading..." : "Not found"}</p>;

  return (
    <div>
      <div className="page-header">
        <h1>Run #{run.id}</h1>
        <Link to="/runs">Back to runs</Link>
      </div>
      <p>
        <strong>Status:</strong> <span className={`badge ${run.status}`}>{run.status}</span>
        {run.trigger === "scheduled" && " (scheduled)"}
      </p>
      {run.error_message && <div className="error">{run.error_message}</div>}
      <p>
        Started: {new Date(run.started_at).toLocaleString()}
        {run.completed_at && ` · Completed: ${new Date(run.completed_at).toLocaleString()}`}
      </p>
      <h2>Documents ({documents.length})</h2>
      {documents.length === 0 && run.status === "completed" && (
        <p>No documents collected (try adding a real search API key for production).</p>
      )}
      {documents.map((d) => (
        <div key={d.id} className="doc-card">
          <h3>
            <a href={d.url} target="_blank" rel="noreferrer">
              {d.title}
            </a>
          </h3>
          <div className="meta">
            {d.source && <span>{d.source}</span>}
            {d.content_type !== "other" && <span> · {d.content_type}</span>}
            {d.relevance_score != null && <span> · score {d.relevance_score.toFixed(2)}</span>}
            {d.matched_entities.length > 0 && (
              <span> · Matched: {d.matched_entities.map((m) => m.entity_name || m.entity_id).join(", ")}</span>
            )}
          </div>
          {d.snippet && <div className="snippet">{d.snippet}</div>}
        </div>
      ))}
    </div>
  );
}
