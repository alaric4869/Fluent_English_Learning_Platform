import { ensureDatabase } from "../../../db/bootstrap";
import { ieltsService } from "../../../modules/app-state/services";
import type { IeltsAction } from "../../../modules/shared/contracts";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    await ensureDatabase();
    return Response.json(await ieltsService.getDashboard(requestUserId(request)));
  } catch (error) {
    return Response.json({ error: message(error) }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    await ensureDatabase();
    const userId = requestUserId(request);
    const action = await readAction(request);
    if (action.type === "save_goal") {
      await ieltsService.saveGoal(userId, action.targetBand, action.examDate);
      return Response.json({ ok: true });
    }
    if (action.type === "start_attempt") {
      const attemptId = await ieltsService.startAttempt(userId, action.bookNumber, action.testNumber, action.skill);
      return Response.json({ ok: true, attemptId });
    }
    if (action.type === "complete_attempt") {
      await ieltsService.completeAttempt(userId, action.attemptId, action.rawScore, action.estimatedBand, action.notes);
      return Response.json({ ok: true });
    }
    return Response.json({ error: "Unsupported IELTS action." }, { status: 400 });
  } catch (error) {
    return Response.json({ error: message(error) }, { status: 400 });
  }
}

async function readAction(request: Request): Promise<IeltsAction> {
  const value = await request.json() as Partial<IeltsAction>;
  if (!value || typeof value !== "object" || typeof value.type !== "string") throw new Error("A valid IELTS action is required.");
  return value as IeltsAction;
}

function requestUserId(request: Request): string {
  return request.headers.get("oai-authenticated-user-id") ?? "local-learner";
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Unable to update IELTS practice.";
}
