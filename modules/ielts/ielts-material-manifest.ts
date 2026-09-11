import type { IeltsSkill } from "../shared/contracts";

export interface IeltsPageRange {
  startPage: number;
  endPage: number;
}

export interface IeltsSectionOption extends IeltsPageRange {
  number: number;
  label: string;
}

export interface IeltsTestOption {
  number: number;
  label: string;
}

type IeltsTestSections = Record<IeltsSkill, IeltsPageRange[]>;
type IeltsBookSections = Record<number, IeltsTestSections>;

/**
 * PDF page numbers, not the page numbers printed in the books. The source PDFs
 * are scans, so these ranges are intentionally kept as content metadata instead
 * of being inferred in React components.
 */
export const IELTS_PAGE_MANIFEST: Record<number, IeltsBookSections> = {
  4: {
    1: {
      listening: ranges([11, 12], [13, 14], [15, 17], [18, 18]),
      reading: ranges([104, 107], [108, 111], [112, 115]),
      writing: ranges([116, 116], [116, 116]),
      speaking: ranges([34, 34]),
    },
    2: {
      listening: ranges([35, 36], [37, 38], [39, 40], [41, 42]),
      reading: ranges([117, 121], [122, 125], [126, 129]),
      writing: ranges([130, 130], [130, 130]),
      speaking: ranges([57, 57]),
    },
    3: {
      listening: ranges([58, 59], [60, 61], [62, 63], [64, 65]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([81, 81]),
    },
    4: {
      listening: ranges([82, 82], [83, 84], [85, 86], [87, 88]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([103, 103]),
    },
  },
  5: {
    1: {
      listening: ranges([11, 12], [13, 13], [14, 15], [16, 16]),
      reading: ranges([102, 105], [106, 109], [110, 113]),
      writing: ranges([114, 114], [114, 114]),
      speaking: ranges([32, 32]),
    },
    2: {
      listening: ranges([33, 33], [34, 35], [36, 36], [37, 38]),
      reading: ranges([115, 119], [120, 123], [124, 127]),
      writing: ranges([128, 128], [128, 128]),
      speaking: ranges([55, 55]),
    },
    3: {
      listening: ranges([56, 57], [58, 59], [60, 60], [61, 62]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([78, 78]),
    },
    4: {
      listening: ranges([79, 79], [80, 81], [82, 83], [84, 85]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([101, 101]),
    },
  },
  6: {
    1: {
      listening: ranges([11, 12], [13, 14], [15, 16], [17, 18]),
      reading: ranges([102, 105], [106, 109], [110, 113]),
      writing: ranges([114, 114], [114, 114]),
      speaking: ranges([33, 33]),
    },
    2: {
      listening: ranges([34, 35], [36, 37], [38, 38], [39, 40]),
      reading: ranges([115, 118], [119, 122], [123, 126]),
      writing: ranges([127, 127], [127, 127]),
      speaking: ranges([55, 55]),
    },
    3: {
      listening: ranges([56, 57], [58, 59], [60, 61], [62, 63]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([78, 78]),
    },
    4: {
      listening: ranges([79, 79], [80, 81], [82, 83], [84, 85]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([101, 101]),
    },
  },
  7: {
    1: {
      listening: ranges([15, 16], [17, 18], [19, 20], [21, 22]),
      reading: ranges([109, 112], [113, 116], [117, 120]),
      writing: ranges([121, 121], [121, 121]),
      speaking: ranges([37, 37]),
    },
    2: {
      listening: ranges([38, 38], [39, 40], [41, 42], [43, 44]),
      reading: ranges([122, 125], [126, 129], [130, 132]),
      writing: ranges([133, 133], [133, 133]),
      speaking: ranges([60, 60]),
    },
    3: {
      listening: ranges([61, 62], [63, 64], [65, 67], [68, 69]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([85, 85]),
    },
    4: {
      listening: ranges([86, 87], [88, 89], [90, 91], [92, 93]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([108, 108]),
    },
  },
  8: {
    1: {
      listening: ranges([9, 10], [11, 12], [13, 14], [15, 16]),
      reading: ranges([103, 106], [107, 110], [111, 114]),
      writing: ranges([115, 115], [115, 115]),
      speaking: ranges([31, 31]),
    },
    2: {
      listening: ranges([32, 33], [34, 35], [36, 37], [38, 39]),
      reading: ranges([116, 119], [120, 123], [124, 127]),
      writing: ranges([128, 128], [128, 128]),
      speaking: ranges([54, 54]),
    },
    3: {
      listening: ranges([55, 57], [58, 59], [60, 61], [62, 63]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([79, 79]),
    },
    4: {
      listening: ranges([80, 80], [81, 82], [83, 84], [85, 86]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([102, 102]),
    },
  },
  9: {
    1: {
      listening: ranges([2, 2], [3, 4], [5, 6], [7, 8]),
      reading: ranges([96, 100], [101, 104], [105, 108]),
      writing: ranges([109, 109], [109, 109]),
      speaking: ranges([24, 24]),
    },
    2: {
      listening: ranges([25, 26], [27, 28], [29, 30], [31, 32]),
      reading: ranges([110, 113], [114, 117], [118, 121]),
      writing: ranges([122, 122], [122, 122]),
      speaking: ranges([47, 47]),
    },
    3: {
      listening: ranges([48, 49], [50, 51], [52, 52], [53, 54]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([70, 70]),
    },
    4: {
      listening: ranges([71, 72], [73, 74], [75, 76], [77, 78]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([95, 95]),
    },
  },
  10: {
    1: {
      listening: ranges([3, 4], [5, 6], [7, 8], [9, 9]),
      reading: ranges([97, 100], [101, 104], [105, 108]),
      writing: ranges([109, 109], [109, 109]),
      speaking: ranges([25, 25]),
    },
    2: {
      listening: ranges([26, 27], [28, 29], [30, 31], [32, 33]),
      reading: ranges([110, 113], [114, 117], [118, 121]),
      writing: ranges([122, 122], [122, 122]),
      speaking: ranges([49, 49]),
    },
    3: {
      listening: ranges([50, 50], [51, 52], [53, 54], [55, 56]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([72, 72]),
    },
    4: {
      listening: ranges([73, 74], [75, 76], [77, 78], [79, 80]),
      reading: ranges(),
      writing: ranges(),
      speaking: ranges([96, 96]),
    },
  },
  11: {
    1: {
      listening: ranges([10, 11], [12, 13], [14, 15], [16, 17]),
      reading: ranges([18, 22], [23, 26], [27, 30]),
      writing: ranges([31, 31], [31, 31]),
      speaking: ranges([32, 32]),
    },
    2: {
      listening: ranges([33, 34], [35, 36], [37, 38], [39, 40]),
      reading: ranges([41, 44], [45, 48], [49, 52]),
      writing: ranges([53, 53], [53, 53]),
      speaking: ranges([54, 54]),
    },
    3: {
      listening: ranges([55, 56], [57, 58], [59, 60], [61, 62]),
      reading: ranges([63, 66], [67, 70], [71, 75]),
      writing: ranges([76, 76], [76, 76]),
      speaking: ranges([77, 77]),
    },
    4: {
      listening: ranges([78, 79], [80, 81], [82, 83], [84, 84]),
      reading: ranges([85, 89], [90, 93], [94, 97]),
      writing: ranges([98, 98], [98, 98]),
      speaking: ranges([99, 99]),
    },
  },
  12: {
    5: {
      listening: ranges([11, 12], [13, 14], [15, 15], [16, 16]),
      reading: ranges([17, 20], [21, 24], [25, 29]),
      writing: ranges([30, 30], [31, 31]),
      speaking: ranges([32, 32]),
    },
    6: {
      listening: ranges([33, 33], [34, 35], [36, 37], [38, 38]),
      reading: ranges([39, 42], [43, 46], [47, 50]),
      writing: ranges([51, 51], [52, 52]),
      speaking: ranges([53, 53]),
    },
    7: {
      listening: ranges([54, 54], [55, 56], [57, 58], [59, 59]),
      reading: ranges([60, 65], [66, 71], [72, 77]),
      writing: ranges([78, 78], [79, 79]),
      speaking: ranges([80, 80]),
    },
    8: {
      listening: ranges([81, 81], [82, 83], [84, 85], [86, 86]),
      reading: ranges([87, 90], [91, 95], [96, 99]),
      writing: ranges([100, 100], [101, 101]),
      speaking: ranges([102, 102]),
    },
  },
  13: {
    1: {
      listening: ranges([3, 3], [4, 5], [6, 7], [8, 8]),
      reading: ranges([9, 12], [13, 16], [17, 20]),
      writing: ranges([21, 21], [22, 22]),
      speaking: ranges([23, 23]),
    },
    2: {
      listening: ranges([24, 24], [25, 26], [27, 28], [29, 29]),
      reading: ranges([30, 33], [34, 37], [38, 42]),
      writing: ranges([43, 43], [44, 44]),
      speaking: ranges([45, 45]),
    },
    3: {
      listening: ranges([46, 46], [47, 48], [49, 50], [51, 51]),
      reading: ranges([52, 55], [56, 59], [60, 64]),
      writing: ranges([65, 65], [66, 66]),
      speaking: ranges([67, 67]),
    },
    4: {
      listening: ranges([68, 68], [69, 70], [71, 72], [73, 73]),
      reading: ranges([74, 77], [78, 81], [82, 85]),
      writing: ranges([86, 86], [87, 87]),
      speaking: ranges([88, 88]),
    },
  },
  14: {
    1: {
      listening: ranges([11, 11], [12, 13], [14, 15], [16, 16]),
      reading: ranges([17, 20], [21, 25], [26, 30]),
      writing: ranges([31, 31], [32, 32]),
      speaking: ranges([33, 33]),
    },
    2: {
      listening: ranges([34, 34], [35, 36], [37, 38], [39, 39]),
      reading: ranges([40, 43], [44, 47], [48, 51]),
      writing: ranges([52, 52], [53, 53]),
      speaking: ranges([54, 54]),
    },
    3: {
      listening: ranges([55, 55], [56, 57], [58, 59], [60, 60]),
      reading: ranges([61, 65], [66, 69], [70, 74]),
      writing: ranges([75, 75], [76, 76]),
      speaking: ranges([77, 77]),
    },
    4: {
      listening: ranges([78, 79], [80, 81], [82, 83], [84, 84]),
      reading: ranges([85, 88], [89, 92], [93, 96]),
      writing: ranges([97, 97], [98, 98]),
      speaking: ranges([99, 99]),
    },
  },
  15: {
    1: {
      listening: ranges([10, 10], [11, 12], [13, 14], [15, 15]),
      reading: ranges([16, 19], [20, 23], [24, 28]),
      writing: ranges([29, 29], [30, 30]),
      speaking: ranges([31, 31]),
    },
    2: {
      listening: ranges([32, 32], [33, 34], [35, 36], [37, 37]),
      reading: ranges([38, 41], [42, 45], [46, 50]),
      writing: ranges([51, 51], [52, 52]),
      speaking: ranges([53, 53]),
    },
    3: {
      listening: ranges([54, 55], [56, 57], [58, 58], [59, 59]),
      reading: ranges([60, 63], [64, 67], [68, 72]),
      writing: ranges([73, 73], [74, 74]),
      speaking: ranges([75, 75]),
    },
    4: {
      listening: ranges([76, 76], [77, 78], [79, 80], [81, 81]),
      reading: ranges([82, 85], [86, 89], [90, 94]),
      writing: ranges([95, 95], [96, 96]),
      speaking: ranges([97, 97]),
    },
  },
  16: {
    1: {
      listening: ranges([13, 13], [14, 15], [16, 17], [18, 18]),
      reading: ranges([19, 22], [23, 26], [27, 31]),
      writing: ranges([32, 32], [33, 33]),
      speaking: ranges([34, 34]),
    },
    2: {
      listening: ranges([35, 35], [36, 37], [38, 39], [40, 40]),
      reading: ranges([41, 44], [45, 48], [49, 53]),
      writing: ranges([54, 54], [55, 55]),
      speaking: ranges([56, 56]),
    },
    3: {
      listening: ranges([57, 57], [58, 59], [60, 61], [62, 62]),
      reading: ranges([63, 66], [67, 70], [71, 75]),
      writing: ranges([76, 76], [77, 77]),
      speaking: ranges([78, 78]),
    },
    4: {
      listening: ranges([79, 79], [80, 81], [82, 83], [84, 84]),
      reading: ranges([85, 88], [89, 92], [93, 97]),
      writing: ranges([98, 98], [99, 99]),
      speaking: ranges([100, 100]),
    },
  },
  17: {
    1: {
      listening: ranges([11, 11], [12, 13], [14, 15], [16, 16]),
      reading: ranges([17, 22], [23, 26], [27, 31]),
      writing: ranges([32, 32], [33, 33]),
      speaking: ranges([34, 34]),
    },
    2: {
      listening: ranges([35, 35], [36, 37], [38, 39], [40, 40]),
      reading: ranges([41, 44], [45, 48], [49, 53]),
      writing: ranges([54, 54], [55, 55]),
      speaking: ranges([56, 56]),
    },
    3: {
      listening: ranges([57, 57], [58, 59], [60, 61], [62, 62]),
      reading: ranges([63, 66], [67, 70], [71, 75]),
      writing: ranges([76, 76], [77, 77]),
      speaking: ranges([78, 78]),
    },
    4: {
      listening: ranges([79, 79], [80, 81], [82, 83], [84, 84]),
      reading: ranges([85, 88], [89, 92], [93, 97]),
      writing: ranges([98, 98], [99, 99]),
      speaking: ranges([100, 100]),
    },
  },
  18: {
    1: {
      listening: ranges([12, 12], [13, 14], [15, 16], [17, 17]),
      reading: ranges([18, 21], [22, 25], [26, 30]),
      writing: ranges([31, 31], [32, 32]),
      speaking: ranges([33, 33]),
    },
    2: {
      listening: ranges([34, 35], [36, 37], [38, 39], [40, 40]),
      reading: ranges([41, 45], [46, 50], [51, 55]),
      writing: ranges([56, 56], [57, 57]),
      speaking: ranges([58, 58]),
    },
    3: {
      listening: ranges([59, 59], [60, 61], [62, 63], [64, 64]),
      reading: ranges([65, 69], [70, 73], [74, 78]),
      writing: ranges([79, 79], [80, 80]),
      speaking: ranges([81, 81]),
    },
    4: {
      listening: ranges([82, 82], [83, 84], [85, 86], [87, 87]),
      reading: ranges([88, 92], [93, 97], [98, 101]),
      writing: ranges([102, 102], [103, 103]),
      speaking: ranges([104, 104]),
    },
  },
  19: {
    1: {
      listening: ranges([12, 12], [13, 14], [15, 16], [17, 17]),
      reading: ranges([18, 21], [22, 25], [26, 30]),
      writing: ranges([31, 31], [32, 32]),
      speaking: ranges([33, 33]),
    },
    2: {
      listening: ranges([34, 35], [36, 37], [38, 39], [40, 40]),
      reading: ranges([41, 44], [45, 48], [49, 53]),
      writing: ranges([54, 54], [55, 55]),
      speaking: ranges([56, 56]),
    },
    3: {
      listening: ranges([57, 58], [59, 60], [61, 62], [63, 63]),
      reading: ranges([64, 67], [68, 71], [72, 75]),
      writing: ranges([76, 76], [77, 77]),
      speaking: ranges([78, 78]),
    },
    4: {
      listening: ranges([79, 79], [80, 81], [82, 83], [84, 84]),
      reading: ranges([85, 88], [89, 93], [94, 98]),
      writing: ranges([99, 99], [100, 100]),
      speaking: ranges([101, 101]),
    },
  },
  20: {
    1: {
      listening: ranges([10, 10], [11, 12], [13, 14], [15, 15]),
      reading: ranges([16, 19], [20, 23], [24, 27]),
      writing: ranges([28, 28], [29, 29]),
      speaking: ranges([30, 30]),
    },
    2: {
      listening: ranges([31, 31], [32, 33], [34, 35], [36, 36]),
      reading: ranges([37, 40], [41, 44], [45, 49]),
      writing: ranges([50, 50], [51, 51]),
      speaking: ranges([52, 52]),
    },
    3: {
      listening: ranges([53, 53], [54, 55], [56, 57], [58, 58]),
      reading: ranges([59, 62], [63, 66], [67, 70]),
      writing: ranges([71, 71], [72, 72]),
      speaking: ranges([73, 73]),
    },
    4: {
      listening: ranges([74, 74], [75, 76], [77, 78], [79, 79]),
      reading: ranges([80, 83], [84, 87], [88, 92]),
      writing: ranges([93, 93], [94, 94]),
      speaking: ranges([95, 95]),
    },
  },
};

const SECTION_LABELS: Record<IeltsSkill, string> = {
  listening: "Part",
  reading: "Section",
  writing: "Task",
  speaking: "Speaking test",
};

export function getIeltsSectionOptions(bookNumber: number, testNumber: number, skill: IeltsSkill): IeltsSectionOption[] {
  const pageRanges = IELTS_PAGE_MANIFEST[bookNumber]?.[testNumber]?.[skill] ?? [];
  return pageRanges.map((pageRange, index) => ({
    ...pageRange,
    number: index + 1,
    label: skill === "speaking" ? SECTION_LABELS.speaking : `${SECTION_LABELS[skill]} ${index + 1}`,
  }));
}

export function getIeltsTestOptions(bookNumber: number, skill: IeltsSkill): IeltsTestOption[] {
  const indexed = Object.entries(IELTS_PAGE_MANIFEST[bookNumber] ?? {})
    .filter(([, test]) => test[skill].length > 0)
    .map(([testNumber]) => Number(testNumber))
    .sort((left, right) => left - right);
  const fallback = bookNumber === 12
    ? [5, 6, 7, 8]
    : bookNumber <= 10 && (skill === "reading" || skill === "writing")
      ? [1, 2]
      : [1, 2, 3, 4];
  return (indexed.length ? indexed : fallback).map((number) => ({
    number,
    label: formatIeltsTestLabel(bookNumber, skill, number),
  }));
}

export function formatIeltsTestLabel(bookNumber: number, skill: IeltsSkill, testNumber: number): string {
  if (bookNumber <= 10 && (skill === "reading" || skill === "writing")) {
    return `GT Test ${testNumber === 1 ? "A" : "B"}`;
  }
  return `Test ${testNumber}`;
}

function ranges(...values: Array<[number, number]>): IeltsPageRange[] {
  return values.map(([startPage, endPage]) => ({ startPage, endPage }));
}
