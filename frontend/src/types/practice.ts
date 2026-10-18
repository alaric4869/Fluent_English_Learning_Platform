export interface WritingDraftPayload {
  response_text: string;
  outline: string;
  active_duration_seconds: number;
  perceived_difficulty: number | null;
  confidence: number | null;
}


export interface WritingWorkspaceResponse {
  resource_id: number;
  resource_title: string;
  description: string;
  test_number: number;
  minimum_words: number;
  recommended_minutes: number;
  task_type: string;
  instructions: string;
  situation: string;
  prompt: string;
  bullet_points: string[];
  closing_instruction: string;
  draft: WritingDraftPayload & {
    id: number | null;
    resource_id: number;
    word_count: number;
    status: string;
    submission_revision: number;
    started_at: string | null;
    submitted_at: string | null;
    updated_at: string | null;
  };
}


export interface SpeakingDraftPayload {
  written_outline: string;
  intended_vocabulary: string[];
  retelling_text: string;
  mistakes: string;
  improved_version: string;
  practice_status: "need_practice" | "good" | "mastered";
  active_duration_seconds: number;
  perceived_difficulty: number | null;
  confidence: number | null;
}


export interface SpeakingWorkspaceResponse {
  resource_id: number;
  resource_title: string;
  description: string;
  test_number: number;
  estimated_duration_minutes: number;
  audio_url: string;
  source_label: string;
  context: string;
  workflow: string[];
  sentences: Array<{
    key: string;
    speaker: string;
    text: string;
    pronunciation_note: string;
    connected_speech_note: string;
    chunks: string[];
    progress: null | {
      practice_status: "need_practice" | "good" | "mastered";
      practice_count: number;
      updated_at: string;
    };
  }>;
  retelling_prompt: string;
  retelling_guidance: string[];
  marked_count: number;
  mastered_count: number;
  draft: SpeakingDraftPayload & {
    id: number | null;
    resource_id: number;
    status: string;
    submission_revision: number;
    started_at: string | null;
    submitted_at: string | null;
    updated_at: string | null;
  };
}


export type ListeningSentenceStatus = "could_not_hear" | "difficult" | "understood" | "mastered";


export interface ListeningWorkspaceResponse {
  resource_id: number;
  title: string;
  description: string;
  topic: string;
  difficulty: string | null;
  resource_type: string;
  estimated_duration_minutes: number;
  is_user_owned: boolean;
  media_kind: "youtube" | "audio" | "local_parts" | "external" | "missing";
  media_url: string | null;
  local_audio_parts: Array<{ number: number; label: string; url: string }>;
  practice_href: string | null;
  sentences: Array<{
    position: number;
    text: string;
    status: ListeningSentenceStatus | "";
    saved_id: number | null;
    review_item_id: number | null;
    next_review_date: string | null;
  }>;
}
