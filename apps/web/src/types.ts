export type EntityType = "company" | "person";
export type RunTrigger = "manual" | "scheduled";
export type RunStatus = "pending" | "running" | "completed" | "failed";
export type ContentType = "news" | "press_release" | "blog" | "other";

export interface Entity {
  id: number;
  name: string;
  type: EntityType;
  aliases: string[];
  created_at: string;
}

export interface Watchlist {
  id: number;
  name: string;
  entity_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface Run {
  id: number;
  watchlist_id: number;
  trigger: RunTrigger;
  status: RunStatus;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface DocumentMatch {
  entity_id: number;
  entity_name?: string;
}

export interface Document {
  id: number;
  run_id: number;
  title: string;
  source: string | null;
  url: string;
  published_at: string | null;
  snippet: string | null;
  content_type: ContentType;
  relevance_score: number | null;
  matched_entities: DocumentMatch[];
  created_at: string;
}
