export interface DueReviewItem {
  review_item_id: number;
  target_type: string;
  target_id: number;
  title: string;
  secondary_text: string;
  answer_label: string;
  answer: string;
  note: string;
  target_label: string;
  mastery_status: string;
  source_title: string;
  due_label: string;
  next_review_date: string;
  review_count: number;
}

export interface VocabularyLibraryItem {
  id: number;
  chunk: string;
  meaning: string;
  example_sentence: string;
  learned_on: string;
  personal_note: string;
  difficulty: string;
  mastery_status: string;
  source_title: string;
  source_context: string;
  tags: string[];
  favorite: boolean;
  saved_for_later: boolean;
  review_item_id: number;
  review_step: number;
  next_review_date: string;
  last_reviewed_at: string | null;
  review_count: number;
}

export interface ReviewWorkspaceResponse {
  today: string;
  due_count: number;
  total_count: number;
  mastered_count: number;
  due_items: DueReviewItem[];
  library_items: VocabularyLibraryItem[];
}

export type ReviewRating = "again" | "hard" | "good" | "easy";

export interface VocabularyPayload {
  chunk: string;
  meaning: string;
  example_sentence: string;
  personal_note: string;
  difficulty: "easy" | "medium" | "hard";
  source_resource_id: number | null;
  source_context: string;
  tags: string[];
}
