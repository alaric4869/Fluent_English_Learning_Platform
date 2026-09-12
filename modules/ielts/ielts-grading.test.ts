import { describe, expect, it } from "vitest";
import { answerMatches, gradeIeltsAnswers } from "./ielts-grading";
import type { IeltsAnswerKey } from "./ielts-question-bank";

describe("IELTS answer grading", () => {
  it("accepts case, spacing, currency and optional words", () => {
    expect(answerMatches("  KING'S ", "Kings/King's")).toBe(true);
    expect(answerMatches("£30", "(£)30/(£)thirty")).toBe(true);
    expect(answerMatches("two hundred thirty-nine", "two hundred (and) thirty-nine")).toBe(true);
    expect(answerMatches("NOT-GIVEN", "NOT GIVEN")).toBe(true);
    expect(answerMatches("07788 136 711", "07788136711")).toBe(true);
  });

  it("grades either-order pairs as a set and rejects duplicates", () => {
    const key: IeltsAnswerKey = {
      bookNumber: 20,
      testNumber: 1,
      skill: "listening",
      answers: [
        { questionNumber: 17, sectionNumber: 2, acceptedAnswers: ["A", "E"], acceptedSet: ["A", "E"], groupId: "17-18" },
        { questionNumber: 18, sectionNumber: 2, acceptedAnswers: ["A", "E"], acceptedSet: ["A", "E"], groupId: "17-18" },
      ],
    };
    expect(gradeIeltsAnswers(key, [
      { questionNumber: 17, sectionNumber: 2, answer: "E" },
      { questionNumber: 18, sectionNumber: 2, answer: "A" },
    ]).rawScore).toBe(2);
    expect(gradeIeltsAnswers(key, [
      { questionNumber: 17, sectionNumber: 2, answer: "A" },
      { questionNumber: 18, sectionNumber: 2, answer: "A" },
    ]).rawScore).toBe(0);
  });

  it("accepts alternatives inside an either-order group", () => {
    const key: IeltsAnswerKey = {
      bookNumber: 4,
      testNumber: 4,
      skill: "listening",
      answers: [
        { questionNumber: 8, sectionNumber: 1, acceptedAnswers: ["tapes", "photos/photographs"], acceptedSet: ["tapes", "photos/photographs"], groupId: "8-9" },
        { questionNumber: 9, sectionNumber: 1, acceptedAnswers: ["tapes", "photos/photographs"], acceptedSet: ["tapes", "photos/photographs"], groupId: "8-9" },
      ],
    };
    expect(gradeIeltsAnswers(key, [
      { questionNumber: 8, sectionNumber: 1, answer: "photographs" },
      { questionNumber: 9, sectionNumber: 1, answer: "tapes" },
    ]).rawScore).toBe(2);
  });
});
