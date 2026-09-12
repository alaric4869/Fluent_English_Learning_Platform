import type { IeltsSkill } from "../shared/contracts";

export interface IeltsAnswerKeyEntry {
  questionNumber: number;
  sectionNumber: number;
  acceptedAnswers: string[];
  groupId?: string;
  acceptedSet?: string[];
  explanationPage?: number;
}

export interface IeltsAnswerKey {
  bookNumber: number;
  testNumber: number;
  skill: Extract<IeltsSkill, "listening" | "reading">;
  answers: IeltsAnswerKeyEntry[];
}

export interface IeltsSubmittedAnswer {
  questionNumber: number;
  sectionNumber: number;
  answer: string;
}

export interface IeltsGradedAnswer extends IeltsSubmittedAnswer {
  isCorrect: boolean;
  correctAnswer: string;
  explanationPage: number | null;
}

export function sectionForQuestion(skill: Extract<IeltsSkill, "listening" | "reading">, questionNumber: number): number {
  if (skill === "listening") return Math.min(4, Math.ceil(questionNumber / 10));
  if (questionNumber <= 14) return 1;
  if (questionNumber <= 27) return 2;
  return 3;
}

export function questionNumbersForSection(skill: Extract<IeltsSkill, "listening" | "reading">, sectionNumber: number): number[] {
  const ranges = skill === "listening"
    ? [[1, 10], [11, 20], [21, 30], [31, 40]]
    : [[1, 14], [15, 27], [28, 40]];
  const range = ranges[sectionNumber - 1];
  if (!range) return [];
  return Array.from({ length: range[1] - range[0] + 1 }, (_, index) => range[0] + index);
}

export function answerKeyId(bookNumber: number, testNumber: number, skill: Extract<IeltsSkill, "listening" | "reading">): string {
  return `${bookNumber}-${testNumber}-${skill}`;
}
