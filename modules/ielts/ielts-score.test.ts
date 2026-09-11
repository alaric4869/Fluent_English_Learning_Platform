import { describe, expect, it } from "vitest";
import { estimateIeltsBand } from "./ielts-score";

describe("estimateIeltsBand", () => {
  it("estimates the listening score needed for the learner's 6.5 target", () => {
    expect(estimateIeltsBand("listening", 26)).toBe(6.5);
    expect(estimateIeltsBand("listening", 30)).toBe(7);
  });

  it("uses the more demanding General Training reading conversion", () => {
    expect(estimateIeltsBand("reading", 30)).toBe(6);
    expect(estimateIeltsBand("reading", 32)).toBe(6.5);
  });

  it("rejects impossible raw scores", () => {
    expect(() => estimateIeltsBand("listening", 41)).toThrow();
  });
});
