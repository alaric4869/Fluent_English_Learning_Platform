import type { IeltsSkill } from "../shared/contracts";
import type { IeltsPageRange } from "./ielts-material-manifest";
import generatedRanges from "./ielts-explanation-manifest.generated.json";

type ObjectiveSkill = Extract<IeltsSkill, "listening" | "reading">;

/**
 * PDF page ranges in the user's local 精讲 books. These are separate from the
 * original test-book ranges because the answer books use their own pagination.
 */
const EXPLANATION_RANGES = generatedRanges satisfies Record<string, IeltsPageRange[]>;

export function getIeltsExplanationRange(
  bookNumber: number,
  testNumber: number,
  skill: ObjectiveSkill,
  sectionNumber: number,
): IeltsPageRange | null {
  return EXPLANATION_RANGES[`${bookNumber}-${testNumber}-${skill}`]?.[sectionNumber - 1] ?? null;
}
