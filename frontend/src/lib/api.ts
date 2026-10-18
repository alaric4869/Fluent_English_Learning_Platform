import type { DashboardResponse, TodayResponse } from "../types/api";
import type { HistoryDay, HistoryResponse, ProgressResponse, WeeklyReviewResponse } from "../types/insights";
import type { NotebookResponse, NotePayload } from "../types/notebook";
import type { ResourceDetail, ResourceLibraryResponse, ResourcePayload, ResourceStatePayload } from "../types/resources";
import type { ReviewRating, ReviewWorkspaceResponse, VocabularyPayload } from "../types/review";
import type { IeltsCatalogResponse, IeltsPracticeWorkspaceResponse, IeltsSubmitResponse } from "../types/ielts";
import type { ListeningSentenceStatus, ListeningWorkspaceResponse, SpeakingDraftPayload, SpeakingWorkspaceResponse, WritingDraftPayload, WritingWorkspaceResponse } from "../types/practice";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
export const BACKEND_PAGE_URL =
  import.meta.env.VITE_BACKEND_PAGE_URL ?? "http://127.0.0.1:8000";


interface ApiErrorBody {
  detail?: string | {
    message?: string;
    missing_questions?: number[];
  };
}


export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body: ApiErrorBody | null,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}


async function requestJson<T>(
  path: string,
  init: RequestInit = {},
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
    signal,
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorBody | null;
    const message = typeof payload?.detail === "string"
      ? payload.detail
      : payload?.detail?.message ?? `Request failed (${response.status})`;
    throw new ApiRequestError(message, response.status, payload);
  }
  return (await response.json()) as T;
}


function queryString(values: Record<string, string | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}


export const frontendApi = {
  dashboard: (signal?: AbortSignal) =>
    requestJson<DashboardResponse>("/api/v1/dashboard", {}, signal),
  today: (signal?: AbortSignal) =>
    requestJson<TodayResponse>("/api/v1/today", {}, signal),
  library: (filters: Record<string, string>, signal?: AbortSignal) =>
    requestJson<ResourceLibraryResponse>(`/api/v1/library${queryString(filters)}`, {}, signal),
  resource: (resourceId: number, signal?: AbortSignal) =>
    requestJson<ResourceDetail>(`/api/v1/library/${resourceId}`, {}, signal),
  createResource: (payload: ResourcePayload) =>
    requestJson<ResourceDetail>("/api/v1/library", { method: "POST", body: JSON.stringify(payload) }),
  updateResource: (resourceId: number, payload: ResourcePayload) =>
    requestJson<ResourceDetail>(`/api/v1/library/${resourceId}`, { method: "PUT", body: JSON.stringify(payload) }),
  updateResourceState: (resourceId: number, payload: ResourceStatePayload) =>
    requestJson<ResourceDetail>(`/api/v1/library/${resourceId}/state`, { method: "PATCH", body: JSON.stringify(payload) }),
  review: (filters: Record<string, string>, signal?: AbortSignal) =>
    requestJson<ReviewWorkspaceResponse>(`/api/v1/review${queryString(filters)}`, {}, signal),
  createVocabulary: (payload: VocabularyPayload) =>
    requestJson("/api/v1/vocabulary", { method: "POST", body: JSON.stringify(payload) }),
  rateReview: (reviewItemId: number, rating: ReviewRating) =>
    requestJson(`/api/v1/reviews/${reviewItemId}/rate`, {
      method: "POST",
      body: JSON.stringify({ rating, request_id: crypto.randomUUID() }),
    }),
  notebook: (filters: Record<string, string>, signal?: AbortSignal) =>
    requestJson<NotebookResponse>(`/api/v1/notebook${queryString(filters)}`, {}, signal),
  createNote: (payload: NotePayload) =>
    requestJson("/api/v1/notebook/notes", { method: "POST", body: JSON.stringify(payload) }),
  updateSentenceStatus: (sentenceId: number, practiceStatus: string) =>
    requestJson(`/api/v1/notebook/sentences/${sentenceId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ practice_status: practiceStatus }),
    }),
  history: (view: string, month: string, signal?: AbortSignal) =>
    requestJson<HistoryResponse>(`/api/v1/history${queryString({ view, month })}`, {}, signal),
  historyDay: (studyDate: string, signal?: AbortSignal) =>
    requestJson<HistoryDay>(`/api/v1/history/${studyDate}`, {}, signal),
  progress: (signal?: AbortSignal) =>
    requestJson<ProgressResponse>("/api/v1/progress", {}, signal),
  weeklyReview: (signal?: AbortSignal) =>
    requestJson<WeeklyReviewResponse>("/api/v1/weekly-review", {}, signal),
  ieltsCatalog: (signal?: AbortSignal) =>
    requestJson<IeltsCatalogResponse>("/api/v1/ielts", {}, signal),
  ieltsWorkspace: (slug: string, signal?: AbortSignal) =>
    requestJson<IeltsPracticeWorkspaceResponse>(`/api/v1/ielts/${slug}`, {}, signal),
  saveIeltsAnswer: (slug: string, questionNumber: number, answer: string) =>
    requestJson(`/api/v1/ielts/${slug}/answers/${questionNumber}`, {
      method: "PUT",
      body: JSON.stringify({ answer }),
    }),
  submitIelts: (slug: string) =>
    requestJson<IeltsSubmitResponse>(`/api/v1/ielts/${slug}/submit`, { method: "POST" }),
  writingWorkspace: (resourceId: number, signal?: AbortSignal) =>
    requestJson<WritingWorkspaceResponse>(`/api/v1/writing/${resourceId}`, {}, signal),
  saveWritingDraft: (resourceId: number, payload: WritingDraftPayload) =>
    requestJson(`/api/v1/writing/${resourceId}/draft`, { method: "PUT", body: JSON.stringify(payload) }),
  submitWriting: (resourceId: number) =>
    requestJson<{ submission_revision: number; word_count: number }>(`/api/v1/writing/${resourceId}/submit`, { method: "POST" }),
  speakingWorkspace: (resourceId: number, signal?: AbortSignal) =>
    requestJson<SpeakingWorkspaceResponse>(`/api/v1/speaking/${resourceId}`, {}, signal),
  saveSpeakingDraft: (resourceId: number, payload: SpeakingDraftPayload) =>
    requestJson(`/api/v1/speaking/${resourceId}/draft`, { method: "PUT", body: JSON.stringify(payload) }),
  markSpeakingSentence: (resourceId: number, sentenceKey: string, practiceStatus: SpeakingDraftPayload["practice_status"]) =>
    requestJson(`/api/v1/speaking/${resourceId}/sentences/${sentenceKey}`, { method: "PUT", body: JSON.stringify({ practice_status: practiceStatus }) }),
  submitSpeaking: (resourceId: number) =>
    requestJson<{ submission_revision: number }>(`/api/v1/speaking/${resourceId}/submit`, { method: "POST" }),
  listeningWorkspace: (resourceId: number, signal?: AbortSignal) =>
    requestJson<ListeningWorkspaceResponse>(`/api/v1/listening/${resourceId}`, {}, signal),
  markListeningSentence: (resourceId: number, sentence: string, practiceStatus: ListeningSentenceStatus) =>
    requestJson<{ review_item_id: number | null; next_review_date: string | null }>(`/api/v1/listening/${resourceId}/sentences`, { method: "POST", body: JSON.stringify({ sentence, practice_status: practiceStatus }) }),
};
