const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  entities: {
    list: () => fetchApi<import("./types").Entity[]>("/entities"),
    create: (body: { name: string; type: "company" | "person"; aliases?: { alias: string }[] }) =>
      fetchApi<import("./types").Entity>("/entities", { method: "POST", body: JSON.stringify(body) }),
    delete: (id: number) => fetchApi<void>(`/entities/${id}`, { method: "DELETE" }),
  },
  watchlists: {
    list: () => fetchApi<import("./types").Watchlist[]>("/watchlists"),
    get: (id: number) => fetchApi<import("./types").Watchlist>(`/watchlists/${id}`),
    create: (body: { name: string; entity_ids: number[] }) =>
      fetchApi<import("./types").Watchlist>("/watchlists", { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: { name?: string; entity_ids?: number[] }) =>
      fetchApi<import("./types").Watchlist>(`/watchlists/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: number) => fetchApi<void>(`/watchlists/${id}`, { method: "DELETE" }),
  },
  runs: {
    list: (watchlistId?: number) =>
      fetchApi<import("./types").Run[]>(`/runs${watchlistId != null ? `?watchlist_id=${watchlistId}` : ""}`),
    get: (id: number) => fetchApi<import("./types").Run>(`/runs/${id}`),
    create: (watchlistId: number, trigger: "manual" | "scheduled" = "manual") =>
      fetchApi<import("./types").Run>("/runs", {
        method: "POST",
        body: JSON.stringify({ watchlist_id: watchlistId, trigger }),
      }),
    documents: (runId: number, entityId?: number) =>
      fetchApi<import("./types").Document[]>(
        `/runs/${runId}/documents${entityId != null ? `?entity_id=${entityId}` : ""}`
      ),
  },
};
