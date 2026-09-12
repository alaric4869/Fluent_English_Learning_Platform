import { classifyIeltsPath, deduplicateIeltsAudio, type ClassifiedIeltsFile } from "./local-resource-catalog";

export interface BrowserFileHandle {
  kind: "file";
  name: string;
  getFile(): Promise<File>;
}

export interface BrowserDirectoryHandle {
  kind: "directory";
  name: string;
  values(): AsyncIterableIterator<BrowserFileHandle | BrowserDirectoryHandle>;
  queryPermission?(options?: { mode?: "read" }): Promise<"granted" | "denied" | "prompt">;
  requestPermission?(options?: { mode?: "read" }): Promise<"granted" | "denied" | "prompt">;
}

export interface LocalIeltsFile extends ClassifiedIeltsFile {
  name: string;
  getFile(): Promise<File>;
}

export interface LocalIeltsCatalog {
  folderName: string;
  books: number[];
  pdfs: LocalIeltsFile[];
  answerPdfs: LocalIeltsFile[];
  audio: LocalIeltsFile[];
  totalAudioFiles: number;
}

const HANDLE_DATABASE = "fluent-local-resources";
const HANDLE_STORE = "directory-handles";
const HANDLE_KEY = "ielts-resources";

export async function chooseResourcesDirectory(): Promise<BrowserDirectoryHandle> {
  const picker = (window as Window & { showDirectoryPicker?: (options?: { mode?: "read" }) => Promise<BrowserDirectoryHandle> }).showDirectoryPicker;
  if (!picker) throw new Error("directory_picker_unavailable");
  const handle = await picker({ mode: "read" });
  await saveDirectoryHandle(handle);
  return handle;
}

export async function restoreResourcesDirectory(): Promise<BrowserDirectoryHandle | null> {
  if (!("indexedDB" in window)) return null;
  const database = await openHandleDatabase();
  return new Promise((resolve, reject) => {
    const request = database.transaction(HANDLE_STORE, "readonly").objectStore(HANDLE_STORE).get(HANDLE_KEY);
    request.onsuccess = () => resolve((request.result as BrowserDirectoryHandle | undefined) ?? null);
    request.onerror = () => reject(request.error);
  });
}

export async function hasReadPermission(handle: BrowserDirectoryHandle): Promise<boolean> {
  if (!handle.queryPermission) return true;
  return (await handle.queryPermission({ mode: "read" })) === "granted";
}

export async function requestReadPermission(handle: BrowserDirectoryHandle): Promise<boolean> {
  if (!handle.requestPermission) return true;
  return (await handle.requestPermission({ mode: "read" })) === "granted";
}

export async function scanResourcesDirectory(handle: BrowserDirectoryHandle): Promise<LocalIeltsCatalog> {
  const files: LocalIeltsFile[] = [];
  await walk(handle, "", files);
  const pdfs = files.filter((file) => file.kind === "pdf" && file.pdfRole === "paper").sort((a, b) => b.bookNumber - a.bookNumber);
  const answerPdfs = files.filter((file) => file.kind === "pdf" && file.pdfRole === "answer").sort((a, b) => b.bookNumber - a.bookNumber);
  const allAudio = files.filter((file) => file.kind === "audio");
  const audio = deduplicateIeltsAudio(allAudio);
  const books = [...new Set([...pdfs, ...answerPdfs, ...audio].map((file) => file.bookNumber))].sort((a, b) => b - a);
  return { folderName: handle.name, books, pdfs, answerPdfs, audio, totalAudioFiles: allAudio.length };
}

export function catalogFromInputFiles(fileList: FileList): LocalIeltsCatalog {
  const files = [...fileList].flatMap((file): LocalIeltsFile[] => {
    const path = file.webkitRelativePath || file.name;
    return classifyLocalFiles(path, file.name, async () => file);
  });
  const pdfs = files.filter((file) => file.kind === "pdf" && file.pdfRole === "paper").sort((a, b) => b.bookNumber - a.bookNumber);
  const answerPdfs = files.filter((file) => file.kind === "pdf" && file.pdfRole === "answer").sort((a, b) => b.bookNumber - a.bookNumber);
  const allAudio = files.filter((file) => file.kind === "audio");
  const audio = deduplicateIeltsAudio(allAudio);
  const books = [...new Set([...pdfs, ...answerPdfs, ...audio].map((file) => file.bookNumber))].sort((a, b) => b - a);
  const folderName = fileList[0]?.webkitRelativePath.split("/")[0] || "resources";
  return { folderName, books, pdfs, answerPdfs, audio, totalAudioFiles: allAudio.length };
}

export function catalogFromBookFiles(fileList: FileList, bookNumber: number): LocalIeltsCatalog {
  const files = [...fileList].flatMap((file): LocalIeltsFile[] => {
    return classifyLocalFiles(`G${bookNumber}/${file.name}`, file.name, async () => file);
  });
  return toCatalog(`剑桥 ${bookNumber}`, files);
}

export function mergeLocalIeltsCatalog(current: LocalIeltsCatalog | null, incoming: LocalIeltsCatalog): LocalIeltsCatalog {
  if (!current) return incoming;
  const pdfByBook = new Map(current.pdfs.map((file) => [file.bookNumber, file]));
  for (const file of incoming.pdfs) pdfByBook.set(file.bookNumber, file);
  const answerPdfByBook = new Map(current.answerPdfs.map((file) => [file.bookNumber, file]));
  for (const file of incoming.answerPdfs) answerPdfByBook.set(file.bookNumber, file);
  const audioBySection = new Map(current.audio.map((file) => [audioKey(file), file]));
  for (const file of incoming.audio) audioBySection.set(audioKey(file), file);
  const audio = [...audioBySection.values()].sort((left, right) =>
    left.bookNumber - right.bookNumber
      || (left.testNumber ?? 0) - (right.testNumber ?? 0)
      || (left.sectionNumber ?? 0) - (right.sectionNumber ?? 0),
  );
  const pdfs = [...pdfByBook.values()].sort((a, b) => b.bookNumber - a.bookNumber);
  const answerPdfs = [...answerPdfByBook.values()].sort((a, b) => b.bookNumber - a.bookNumber);
  const books = [...new Set([...pdfs, ...answerPdfs, ...audio].map((file) => file.bookNumber))].sort((a, b) => b - a);
  return {
    folderName: current.folderName === incoming.folderName ? current.folderName : "已选择的本地资料",
    books,
    pdfs,
    answerPdfs,
    audio,
    totalAudioFiles: Math.max(current.totalAudioFiles, incoming.totalAudioFiles, audio.length),
  };
}

function audioKey(file: LocalIeltsFile): string {
  return `${file.bookNumber}-${file.testNumber}-${file.sectionNumber}`;
}

async function walk(directory: BrowserDirectoryHandle, prefix: string, files: LocalIeltsFile[]): Promise<void> {
  for await (const entry of directory.values()) {
    const path = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.kind === "directory") {
      await walk(entry, path, files);
      continue;
    }
    files.push(...classifyLocalFiles(path, entry.name, () => entry.getFile()));
  }
}

function classifyLocalFiles(path: string, name: string, getFile: () => Promise<File>): LocalIeltsFile[] {
  const classified = classifyIeltsPath(path);
  if (classified) return [{ ...classified, name, getFile }];
  if (/\.pdf$/i.test(path) && /精讲\s*456|456\s*合辑/i.test(path)) {
    return [4, 5, 6].map((bookNumber) => ({
      kind: "pdf" as const,
      path,
      bookNumber,
      testNumber: null,
      sectionNumber: null,
      pdfRole: "answer" as const,
      name,
      getFile,
    }));
  }
  return [];
}

function toCatalog(folderName: string, files: LocalIeltsFile[]): LocalIeltsCatalog {
  const pdfs = files.filter((file) => file.kind === "pdf" && file.pdfRole === "paper").sort((a, b) => b.bookNumber - a.bookNumber);
  const answerPdfs = files.filter((file) => file.kind === "pdf" && file.pdfRole === "answer").sort((a, b) => b.bookNumber - a.bookNumber);
  const allAudio = files.filter((file) => file.kind === "audio");
  const audio = deduplicateIeltsAudio(allAudio);
  const books = [...new Set([...pdfs, ...answerPdfs, ...audio].map((file) => file.bookNumber))].sort((a, b) => b - a);
  return { folderName, books, pdfs, answerPdfs, audio, totalAudioFiles: allAudio.length };
}

async function saveDirectoryHandle(handle: BrowserDirectoryHandle): Promise<void> {
  if (!("indexedDB" in window)) return;
  const database = await openHandleDatabase();
  await new Promise<void>((resolve, reject) => {
    const request = database.transaction(HANDLE_STORE, "readwrite").objectStore(HANDLE_STORE).put(handle, HANDLE_KEY);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function openHandleDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(HANDLE_DATABASE, 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(HANDLE_STORE)) request.result.createObjectStore(HANDLE_STORE);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
