export type LocalIeltsFileKind = "pdf" | "audio";
export type LocalIeltsPdfRole = "paper" | "answer";

export interface ClassifiedIeltsFile {
  kind: LocalIeltsFileKind;
  path: string;
  bookNumber: number;
  testNumber: number | null;
  sectionNumber: number | null;
  pdfRole: LocalIeltsPdfRole | null;
}

export function classifyIeltsPath(path: string): ClassifiedIeltsFile | null {
  const normalized = path.replaceAll("\\", "/");
  const lower = normalized.toLowerCase();
  const kind = lower.endsWith(".pdf") ? "pdf" : /\.(mp3|m4a|wav|aac)$/.test(lower) ? "audio" : null;
  if (!kind) return null;
  const bookNumber = findBookNumber(normalized, kind);
  if (!bookNumber) return null;
  if (kind === "pdf") {
    const pdfRole = /(?:^|\/)answer(?:\/|$)/i.test(normalized) || /精讲|解析/.test(normalized) ? "answer" : "paper";
    return { kind, path: normalized, bookNumber, testNumber: null, sectionNumber: null, pdfRole };
  }
  const location = findTestAndSection(normalized);
  if (!location) return null;
  return { kind, path: normalized, bookNumber, ...location, pdfRole: null };
}

export function deduplicateIeltsAudio<T extends ClassifiedIeltsFile>(files: T[]): T[] {
  const unique = new Map<string, T>();
  for (const file of files) {
    if (file.kind !== "audio" || file.testNumber === null || file.sectionNumber === null) continue;
    const key = `${file.bookNumber}-${file.testNumber}-${file.sectionNumber}`;
    const current = unique.get(key);
    if (!current || audioPathPriority(file.path) > audioPathPriority(current.path)) unique.set(key, file);
  }
  return [...unique.values()].sort((a, b) =>
    a.bookNumber - b.bookNumber || (a.testNumber ?? 0) - (b.testNumber ?? 0) || (a.sectionNumber ?? 0) - (b.sectionNumber ?? 0),
  );
}

function findBookNumber(path: string, kind: LocalIeltsFileKind): number | null {
  const parts = path.split("/").filter(Boolean);
  const target = kind === "audio" ? parts.find((part) => /(?:听力|音频|剑桥|^\d{1,2}$)/i.test(part)) ?? parts[0] : parts.at(-1) ?? path;
  const patterns = [/(?:IELTS|G|真题|听力|剑桥|剑)[^\d]{0,8}(\d{1,2})/i, /^(\d{1,2})(?:音频|听力|[-_.])/i];
  for (const pattern of patterns) {
    const value = Number(target.match(pattern)?.[1]);
    if (value >= 4 && value <= 20) return value;
  }
  return null;
}

function findTestAndSection(path: string): { testNumber: number; sectionNumber: number } | null {
  const stem = path.replace(/\.[^.]+$/, "");
  let test = numberFrom(stem, /test(?:s)?\s*[_ .-]*(\d)/i);
  let section = numberFrom(stem, /(?:section|seciton|secton|audio|part)\s*[_ .-]*(\d)/i);

  const compact = stem.match(/(?:^|[-_/])(?:C?\d{1,2}[-_])?T(\d)[-_]?S?(?:[-_]?P)?(\d)(?:$|[-_/])/i)
    ?? stem.match(/\d{1,2}T(\d)S(\d)$/i);
  if (compact) {
    test ??= Number(compact[1]);
    section ??= Number(compact[2]);
  }

  const dashOnly = stem.match(/(?:^|\/)(?:\d{1,2}-)?(\d)-(\d)$/);
  if (dashOnly) {
    test ??= Number(dashOnly[1]);
    section ??= Number(dashOnly[2]);
  }

  if (section === null) section = numberFrom(stem, /test\s*\d+\s*-\s*(\d)$/i);
  if (test === null || section === null || test < 1 || test > 8 || section < 1 || section > 4) return null;
  return { testNumber: test, sectionNumber: section };
}

function numberFrom(value: string, pattern: RegExp): number | null {
  const match = value.match(pattern);
  return match ? Number(match[1]) : null;
}

function audioPathPriority(path: string): number {
  if (path.includes("/20音频/") || path.startsWith("20音频/")) return 1000;
  return 500 - path.length;
}
