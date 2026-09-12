import { describe, expect, it } from "vitest";
import { IELTS_ANSWER_KEYS } from "./ielts-answer-keys.generated";
import { getIeltsExplanationRange } from "./ielts-explanation-manifest";
import { IELTS_PAGE_MANIFEST } from "./ielts-material-manifest";

describe("IELTS objective answer keys", () => {
  it("covers every indexed Listening and General Training Reading paper", () => {
    const expectedKeys: string[] = [];
    for (const [bookNumber, book] of Object.entries(IELTS_PAGE_MANIFEST)) {
      for (const [testNumber, test] of Object.entries(book)) {
        if (test.listening.length) expectedKeys.push(`${bookNumber}-${testNumber}-listening`);
        if (test.reading.length) expectedKeys.push(`${bookNumber}-${testNumber}-reading`);
      }
    }

    expect([...IELTS_ANSWER_KEYS.keys()].sort()).toEqual(expectedKeys.sort());
  });

  it("contains exactly one non-empty answer for questions 1–40", () => {
    for (const [keyId, key] of IELTS_ANSWER_KEYS) {
      expect(key.answers, keyId).toHaveLength(40);
      expect(key.answers.map((answer) => answer.questionNumber), keyId).toEqual(
        Array.from({ length: 40 }, (_, index) => index + 1),
      );
      for (const answer of key.answers) {
        expect(answer.acceptedAnswers.length, `${keyId} question ${answer.questionNumber}`).toBeGreaterThan(0);
        expect(answer.acceptedAnswers.every((value) => value.trim().length > 0), `${keyId} question ${answer.questionNumber}`).toBe(true);
      }
    }
  });

  it("keeps either-order groups internally consistent", () => {
    for (const [keyId, key] of IELTS_ANSWER_KEYS) {
      const groups = new Map<string, typeof key.answers>();
      for (const answer of key.answers) {
        if (!answer.groupId) continue;
        groups.set(answer.groupId, [...(groups.get(answer.groupId) ?? []), answer]);
      }
      for (const [groupId, answers] of groups) {
        const expectedSet = answers[0]?.acceptedSet;
        expect(expectedSet, `${keyId} group ${groupId}`).toBeDefined();
        expect(answers, `${keyId} group ${groupId}`).toHaveLength(expectedSet?.length ?? 0);
        expect(answers.every((answer) => JSON.stringify(answer.acceptedSet) === JSON.stringify(expectedSet)), `${keyId} group ${groupId}`).toBe(true);
      }
    }
  });

  it("links every objective section to a valid local explanation range", () => {
    for (const [keyId, key] of IELTS_ANSWER_KEYS) {
      const sectionCount = key.skill === "listening" ? 4 : 3;
      for (let section = 1; section <= sectionCount; section += 1) {
        const range = getIeltsExplanationRange(key.bookNumber, key.testNumber, key.skill, section);
        expect(range, `${keyId} section ${section}`).not.toBeNull();
        expect(range?.startPage, `${keyId} section ${section}`).toBeGreaterThan(0);
        expect(range?.endPage, `${keyId} section ${section}`).toBeGreaterThanOrEqual(range?.startPage ?? 0);
      }
    }
  });
});
