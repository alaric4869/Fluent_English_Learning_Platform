import type { IeltsAnswerKey, IeltsGradedAnswer, IeltsSubmittedAnswer } from "./ielts-question-bank";

export interface IeltsGradeResult {
  rawScore: number;
  answers: IeltsGradedAnswer[];
}

export function gradeIeltsAnswers(answerKey: IeltsAnswerKey, submitted: IeltsSubmittedAnswer[]): IeltsGradeResult {
  const responseByQuestion = new Map(submitted.map((item) => [item.questionNumber, item.answer]));
  const grouped = new Map<string, typeof answerKey.answers>();
  for (const entry of answerKey.answers) {
    if (!entry.groupId) continue;
    const current = grouped.get(entry.groupId) ?? [];
    current.push(entry);
    grouped.set(entry.groupId, current);
  }

  const groupCorrect = new Map<string, boolean>();
  for (const [groupId, entries] of grouped) {
    const expected = entries[0]?.acceptedSet ?? [];
    const actual = entries.map((entry) => responseByQuestion.get(entry.questionNumber) ?? "");
    groupCorrect.set(groupId, unorderedAnswersMatch(actual, expected));
  }

  const answers = answerKey.answers.map((entry): IeltsGradedAnswer => {
    const answer = responseByQuestion.get(entry.questionNumber)?.trim() ?? "";
    const isCorrect = entry.groupId
      ? groupCorrect.get(entry.groupId) === true
      : entry.acceptedAnswers.some((candidate) => answerMatches(answer, candidate));
    return {
      questionNumber: entry.questionNumber,
      sectionNumber: entry.sectionNumber,
      answer,
      isCorrect,
      correctAnswer: entry.acceptedSet?.join(" / ") ?? entry.acceptedAnswers.join(" / "),
      explanationPage: entry.explanationPage ?? null,
    };
  });

  return { rawScore: answers.filter((answer) => answer.isCorrect).length, answers };
}

function unorderedAnswersMatch(actual: string[], expected: string[]): boolean {
  if (actual.length !== expected.length || actual.some((answer) => !normalizeIeltsAnswer(answer))) return false;

  const used = new Set<number>();
  const matchFrom = (actualIndex: number): boolean => {
    if (actualIndex === actual.length) return true;
    for (let expectedIndex = 0; expectedIndex < expected.length; expectedIndex += 1) {
      if (used.has(expectedIndex) || !answerMatches(actual[actualIndex], expected[expectedIndex])) continue;
      used.add(expectedIndex);
      if (matchFrom(actualIndex + 1)) return true;
      used.delete(expectedIndex);
    }
    return false;
  };

  return matchFrom(0);
}

export function answerMatches(submitted: string, expected: string): boolean {
  const normalized = normalizeIeltsAnswer(submitted);
  if (!normalized) return false;
  return expandExpectedAnswer(expected).some((candidate) => normalizeIeltsAnswer(candidate) === normalized);
}

export function normalizeIeltsAnswer(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("en")
    .replace(/[’‘]/g, "'")
    .replace(/[£$]/g, "")
    .replace(/[^a-z0-9]/g, "");
}

function expandExpectedAnswer(value: string): string[] {
  const alternatives = value.split("/").map((part) => part.trim()).filter(Boolean);
  return alternatives.flatMap((alternative) => expandParenthetical(alternative));
}

function expandParenthetical(value: string): string[] {
  const match = value.match(/\(([^)]+)\)/);
  if (!match || match.index === undefined) return [value];
  const before = value.slice(0, match.index);
  const after = value.slice(match.index + match[0].length);
  const withOptional = `${before}${match[1]}${after}`;
  const withoutOptional = `${before}${after}`;
  return [...expandParenthetical(withOptional), ...expandParenthetical(withoutOptional)];
}
