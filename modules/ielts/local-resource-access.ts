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
  const pdfs = files.filter((file) => file.kind === "pdf").sort((a, b) => b.bookNumber - a.bookNumber);
  const allAudio = files.filter((file) => file.kind === "audio");
  const audio = deduplicateIeltsAudio(allAudio);
  const books = [...new Set([...pdfs, ...audio].map((file) => file.bookNumber))].sort((a, b) => b - a);
  return { folderName: handle.name, books, pdfs, audio, totalAudioFiles: allAudio.length };
}

export function catalogFromInputFiles(fileList: FileList): LocalIeltsCatalog {
  const files = [...fileList].flatMap((file): LocalIeltsFile[] => {
    const path = file.webkitRelativePath || file.name;
    const classified = classifyIeltsPath(path);
    return classified ? [{ ...classified, name: file.name, getFile: async () => file }] : [];
  });
  const pdfs = files.filter((file) => file.kind === "pdf").sort((a, b) => b.bookNumber - a.bookNumber);
  const allAudio = files.filter((file) => file.kind === "audio");
  const audio = deduplicateIeltsAudio(allAudio);
  const books = [...new Set([...pdfs, ...audio].map((file) => file.bookNumber))].sort((a, b) => b - a);
  const folderName = fileList[0]?.webkitRelativePath.split("/")[0] || "resources";
  return { folderName, books, pdfs, audio, totalAudioFiles: allAudio.length };
}

async function walk(directory: BrowserDirectoryHandle, prefix: string, files: LocalIeltsFile[]): Promise<void> {
  for await (const entry of directory.values()) {
    const path = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.kind === "directory") {
      await walk(entry, path, files);
      continue;
    }
    const classified = classifyIeltsPath(path);
    if (classified) files.push({ ...classified, name: entry.name, getFile: () => entry.getFile() });
  }
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
