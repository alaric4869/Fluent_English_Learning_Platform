export interface NotebookNote {
  id: number;
  note_type: string;
  type_label: string;
  title: string;
  content: string;
  source_context: string;
  tags: string[];
  favorite: boolean;
  saved_for_later: boolean;
  created_at: string;
}

export interface NotebookSentence {
  id: number;
  sentence: string;
  meaning: string;
  learned_on: string;
  practice_status: string;
  status_label: string;
  note: string;
  source_context: string;
  review_item_id: number | null;
  next_review_date: string | null;
  review_count: number;
  mastery_status: string | null;
}

export interface NotebookRetelling {
  id: number;
  prompt: string;
  written_outline: string;
  intended_vocabulary: string[];
  retelling_text: string;
  mistakes: string;
  improved_version: string;
  practice_status: string;
  status_label: string;
  source_context: string;
  created_at: string;
}

export interface NotebookResponse {
  counts: { notes: number; sentences: number; retellings: number };
  notes: NotebookNote[];
  sentences: NotebookSentence[];
  retellings: NotebookRetelling[];
}

export interface NotePayload {
  note_type: string;
  title: string;
  content: string;
  source_resource_id: number | null;
  source_context: string;
  tags: string[];
}
