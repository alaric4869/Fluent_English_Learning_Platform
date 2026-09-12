import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";

test("server bundle exports the Fluent application", async () => {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  const response = await worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Fluent/);
  assert.match(html, /Daily English/);
  assert.doesNotMatch(html, /codex-preview/);
});

test("client bundle uses a deployable PDF worker URL", async () => {
  const chunksDirectory = new URL("../dist/client/_next/static/chunks/", import.meta.url);
  const chunkNames = (await readdir(chunksDirectory)).filter((name) => name.endsWith(".js"));
  const chunkSources = await Promise.all(chunkNames.map((name) => readFile(new URL(name, chunksDirectory), "utf8")));
  const applicationChunk = chunkSources.find((source) => source.includes("/vendor/pdfjs/pdf.worker.min.mjs"));

  assert.ok(applicationChunk, "Expected the PDF worker asset URL in the application bundle");
  assert.doesNotMatch(applicationChunk, /file:\/\/\/.*pdf\.worker/);
  const workerSource = await readFile(new URL("../dist/client/vendor/pdfjs/pdf.worker.min.mjs", import.meta.url), "utf8");
  assert.match(workerSource, /Mozilla Foundation/);
});
