export interface ResourceSummary {
  id: number;
  title: string;
  resource_type: string;
  skill: string;
  topic: string;
  difficulty: string | null;
  estimated_duration_minutes: number;
  source_url: string | null;
  description: string;
  tags: string[];
  priority: number;
  favorite: boolean;
  saved_for_later: boolean;
  archived: boolean;
  is_user_owned: boolean;
  last_studied_at: string | null;
  completed_session_count: number;
  start_href: string | null;
}

export interface ResourceDetail extends ResourceSummary {
  content_text: string;
  transcript: string;
  notes: string;
}

export interface ResourceLibraryResponse {
  view: "all" | "favorites" | "saved" | "archived";
  total_count: number;
  counts: { all: number; favorites: number; saved: number; archived: number };
  facets: { resource_types: string[]; topics: string[]; difficulties: string[] };
  items: ResourceSummary[];
}

export interface ResourcePayload {
  title: string;
  resource_type: string;
  skill: string;
  topic: string;
  difficulty: string | null;
  estimated_duration_minutes: number;
  source_url: string | null;
  description: string;
  content_text: string;
  transcript: string;
  notes: string;
  tags: string[];
  priority: number;
}

export interface ResourceStatePayload {
  favorite?: boolean;
  saved_for_later?: boolean;
  archived?: boolean;
}
