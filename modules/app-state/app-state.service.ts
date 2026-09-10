import type { AppStateDto } from "../shared/contracts";
import { artifactService, notebookService, progressService, resourceService, reviewService, studyPlanService } from "./services";

export async function getAppState(userId: string, date: string): Promise<AppStateDto> {
  const today = await studyPlanService.getOrCreateToday(userId, date);
  const [dueReviews, resources, vocabulary, savedSentences, notebook, history] = await Promise.all([
    reviewService.listDue(userId, date),
    resourceService.list(userId),
    artifactService.listVocabulary(userId),
    artifactService.listSavedSentences(userId),
    notebookService.list(userId),
    progressService.getHistory(userId),
  ]);
  const progress = await progressService.getProgress(userId, date, history);
  return {
    today: {
      date: today.date,
      theme: today.theme,
      targetMinutes: today.targetMinutes,
      adaptationReasons: today.adaptationReasons,
      planItems: today.planItems,
    },
    dueReviews,
    resources,
    vocabulary,
    savedSentences,
    notebook,
    history,
    progress,
  };
}
