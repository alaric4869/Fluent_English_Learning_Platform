import type { IeltsSkill } from "../shared/contracts";

const LISTENING_THRESHOLDS: ReadonlyArray<readonly [number, number]> = [
  [39, 9], [37, 8.5], [35, 8], [32, 7.5], [30, 7], [26, 6.5], [23, 6],
  [18, 5.5], [16, 5], [13, 4.5], [10, 4], [8, 3.5], [6, 3], [4, 2.5],
];

const GENERAL_READING_THRESHOLDS: ReadonlyArray<readonly [number, number]> = [
  [40, 9], [39, 8.5], [38, 8], [36, 7.5], [34, 7], [32, 6.5], [30, 6],
  [27, 5.5], [23, 5], [19, 4.5], [15, 4], [12, 3.5], [9, 3], [6, 2.5],
];

export function estimateIeltsBand(skill: IeltsSkill, rawScore: number): number | null {
  if (skill !== "listening" && skill !== "reading") return null;
  if (!Number.isInteger(rawScore) || rawScore < 0 || rawScore > 40) {
    throw new Error("Raw score must be a whole number between 0 and 40.");
  }
  const table = skill === "listening" ? LISTENING_THRESHOLDS : GENERAL_READING_THRESHOLDS;
  return table.find(([minimum]) => rawScore >= minimum)?.[1] ?? 0;
}
