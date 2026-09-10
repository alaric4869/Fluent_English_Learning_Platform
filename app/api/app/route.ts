import { ensureDatabase, ensureUserSeed } from "../../../db/bootstrap";
import { getAppState } from "../../../modules/app-state/app-state.service";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const date = normalizeDate(url.searchParams.get("date"));
    const userId = requestUserId(request);
    await ensureDatabase();
    await ensureUserSeed(userId, date);
    return Response.json(await getAppState(userId, date));
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Unable to load your learning dashboard." }, { status: 500 });
  }
}

function normalizeDate(value: string | null): string {
  if (value && /^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  return new Date().toISOString().slice(0, 10);
}

function requestUserId(request: Request): string {
  return request.headers.get("oai-authenticated-user-id") ?? "local-learner";
}
