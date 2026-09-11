import { describe, expect, it } from "vitest";
import { IELTS_PAGE_MANIFEST, getIeltsSectionOptions, getIeltsTestOptions } from "./ielts-material-manifest";

describe("IELTS PDF page manifest", () => {
  it("indexes every supplied Cambridge General Training book", () => {
    expect(Object.keys(IELTS_PAGE_MANIFEST).map(Number).sort((left, right) => left - right)).toEqual(
      Array.from({ length: 17 }, (_, index) => index + 4),
    );
  });

  it("returns only the pages for a selected listening part", () => {
    const parts = getIeltsSectionOptions(20, 1, "listening");
    expect(parts).toHaveLength(4);
    expect(parts[1]).toMatchObject({ label: "Part 2", startPage: 11, endPage: 12 });
  });

  it("uses the three General Training reading sections", () => {
    expect(getIeltsSectionOptions(20, 4, "reading")).toEqual([
      { number: 1, label: "Section 1", startPage: 80, endPage: 83 },
      { number: 2, label: "Section 2", startPage: 84, endPage: 87 },
      { number: 3, label: "Section 3", startPage: 88, endPage: 92 },
    ]);
  });

  it("returns an empty list for material that has not been indexed", () => {
    expect(getIeltsSectionOptions(3, 1, "reading")).toEqual([]);
  });

  it("keeps older General Training reading papers separate from Academic tests", () => {
    expect(getIeltsTestOptions(8, "reading")).toEqual([
      { number: 1, label: "GT Test A" },
      { number: 2, label: "GT Test B" },
    ]);
    expect(getIeltsTestOptions(8, "listening").map((test) => test.number)).toEqual([1, 2, 3, 4]);
    expect(getIeltsTestOptions(11, "reading").map((test) => test.label)).toEqual([
      "Test 1", "Test 2", "Test 3", "Test 4",
    ]);
  });

  it("preserves Cambridge 12's printed Test 5–8 numbering", () => {
    expect(getIeltsTestOptions(12, "listening").map((test) => test.label)).toEqual([
      "Test 5", "Test 6", "Test 7", "Test 8",
    ]);
  });

  it("contains valid non-overlapping ranges for every indexed skill", () => {
    for (const book of Object.values(IELTS_PAGE_MANIFEST)) {
      for (const test of Object.values(book)) {
        for (const ranges of Object.values(test)) {
          for (const [index, range] of ranges.entries()) {
            expect(range.startPage).toBeGreaterThan(0);
            expect(range.endPage).toBeGreaterThanOrEqual(range.startPage);
            if (index > 0) expect(range.startPage).toBeGreaterThanOrEqual(ranges[index - 1].startPage);
          }
        }
      }
    }
  });
});
