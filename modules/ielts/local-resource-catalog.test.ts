import { describe, expect, it } from "vitest";
import { classifyIeltsPath, deduplicateIeltsAudio } from "./local-resource-catalog";

describe("local IELTS resource catalog", () => {
  it.each([
    ["ielts_paper/G4真题.pdf", "pdf", 4, null, null],
    ["ielts_paper/G真题12.pdf", "pdf", 12, null, null],
    ["ielts_paper/剑19（G类）.pdf", "pdf", 19, null, null],
    ["listening/【听力13】剑桥雅思13听力音频/test2/Tests2_seciton2.mp3", "audio", 13, 2, 2],
    ["listening/剑桥15/Test  1/IELTS15_test1_audio4.mp3", "audio", 15, 1, 4],
    ["listening/17听力音频/C17-T4-P1.mp3", "audio", 17, 4, 1],
    ["listening/剑18音频/18-3-3.mp3", "audio", 18, 3, 3],
    ["listening/19音频/Test3 Part2.mp3", "audio", 19, 3, 2],
    ["listening/20音频/20T2S1.mp3", "audio", 20, 2, 1],
  ])("classifies %s", (path, kind, book, test, section) => {
    expect(classifyIeltsPath(path)).toMatchObject({ kind, bookNumber: book, testNumber: test, sectionNumber: section });
  });

  it("prefers the clean volume 20 copy when duplicate sections exist", () => {
    const first = classifyIeltsPath("listening/剑20 听力音频 T1-T4/T1S1.mp3");
    const second = classifyIeltsPath("listening/20音频/20T1S1.mp3");
    expect(deduplicateIeltsAudio([first!, second!])).toHaveLength(1);
    expect(deduplicateIeltsAudio([first!, second!])[0].path).toContain("/20音频/");
  });
});
