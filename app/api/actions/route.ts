import { ensureDatabase } from "../../../db/bootstrap";
import { artifactService, notebookService, resourceService, reviewService, studyPlanService } from "../../../modules/app-state/services";
import type { AppAction } from "../../../modules/shared/contracts";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    await ensureDatabase();
    const userId = request.headers.get("oai-authenticated-user-id") ?? "local-learner";
    const action = await readAction(request);

    switch (action.type) {
      case "start_session":
        await studyPlanService.start(userId, action.planItemId);
        break;
      case "complete_plan_item":
        await studyPlanService.complete(userId, action.planItemId, action.activeSeconds);
        break;
      case "save_plan_notes":
        await studyPlanService.saveNotes(userId, action.planItemId, action.notes);
        break;
      case "rate_plan_item":
        await studyPlanService.rate(userId, action.planItemId, action.difficulty, action.confidence);
        break;
      case "replace_resource":
        await studyPlanService.replace(userId, action.planItemId);
        break;
      case "toggle_resource_favorite":
        await resourceService.toggleFavorite(userId, action.resourceId);
        break;
      case "archive_resource":
        await resourceService.archive(userId, action.resourceId);
        break;
      case "add_resource":
        await resourceService.create(userId, action.resource);
        break;
      case "update_resource":
        await resourceService.update(userId, action.resourceId, action.changes);
        break;
      case "add_vocabulary":
        await artifactService.addVocabulary({ userId, ...action });
        break;
      case "save_sentence":
        await artifactService.saveSentence({ userId, ...action });
        break;
      case "rate_review":
        await reviewService.rate(userId, action.reviewItemId, action.rating, action.date);
        break;
      case "add_notebook_entry":
        await notebookService.add({
          userId,
          type: action.entryType,
          title: action.title,
          content: action.content,
          sourceResourceId: action.sourceResourceId,
        });
        break;
      default:
        return Response.json({ error: "Unsupported action." }, { status: 400 });
    }

    return Response.json({ ok: true });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Unable to save this change." }, { status: 400 });
  }
}

async function readAction(request: Request): Promise<AppAction> {
  const value = await request.json() as Partial<AppAction>;
  if (!value || typeof value !== "object" || typeof value.type !== "string") {
    throw new Error("A valid action is required.");
  }
  return value as AppAction;
}
