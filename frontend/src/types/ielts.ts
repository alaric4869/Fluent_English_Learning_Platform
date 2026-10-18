export type IeltsSkill = "listening" | "reading" | "speaking" | "writing";


export interface IeltsModuleSummary {
  key: string;
  title: string;
  description: string;
  skill: IeltsSkill;
  test_number: number;
  duration_minutes: number;
  question_count: number | null;
  section_count: number | null;
  detail_label: string;
  workspace_href: string;
  migrated: boolean;
}


export interface IeltsCatalogResponse {
  target_band: string;
  exam_timing: string;
  module_count: number;
  modules: IeltsModuleSummary[];
}


export interface IeltsQuestionOption {
  key: string;
  text: string;
}


export interface IeltsQuestion {
  number: number;
  prompt: string;
  question_type: "text" | "single_choice" | "true_false_not_given";
  options: IeltsQuestionOption[];
  answer_group: string | null;
}


export interface ContentPart {
  text: string | null;
  answer: number | null;
}


export interface TableBlock {
  kind: "table";
  title: string;
  headers: string[];
  rows: Array<{ cells: ContentPart[][] }>;
}


export interface PassageBlock {
  kind: "passage" | "notice" | "text";
  title: string;
  paragraphs: string[];
}


export interface FigureBlock {
  kind: "figure";
  title: string;
  asset_path: string;
  alt: string;
  caption: string;
  answer_numbers: number[];
}


export interface FlowchartBlock {
  kind: "flowchart";
  title: string;
  nodes: Array<{ parts: ContentPart[] }>;
}


export interface NotesBlock {
  kind: "notes";
  title: string;
  lead: ContentPart[];
  sections: Array<{
    heading: string;
    items: Array<{ level: number; parts: ContentPart[] }>;
  }>;
}


export type IeltsContentBlock =
  | TableBlock
  | PassageBlock
  | FigureBlock
  | FlowchartBlock
  | NotesBlock;


export interface IeltsQuestionResult {
  number: number;
  submitted_answer: string;
  correct_answers: string[];
  is_correct: boolean;
  explanation: string;
}


export interface IeltsSection {
  id: number;
  order_index: number;
  title: string;
  instructions: string;
  has_audio: boolean;
  audio_url: string | null;
  content_blocks: IeltsContentBlock[];
  source_blocks: IeltsContentBlock[];
  question_blocks: IeltsContentBlock[];
  embedded_question_numbers: number[];
  questions: IeltsQuestion[];
}


export interface IeltsPracticeWorkspaceResponse {
  slug: string;
  book_number: number;
  test_number: number;
  skill: "listening" | "reading";
  title: string;
  description: string;
  duration_minutes: number;
  question_count: number;
  sections: IeltsSection[];
  attempt: {
    id: number;
    status: string;
    answers: Record<string, string>;
    results: IeltsQuestionResult[];
    score: number | null;
    submission_revision: number;
    started_at: string;
    updated_at: string;
    submitted_at: string | null;
  };
}


export interface IeltsSubmitResponse {
  attempt_id: number;
  score: number;
  total: number;
  status: string;
  questions: IeltsQuestionResult[];
}
