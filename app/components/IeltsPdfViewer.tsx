"use client";

import { useEffect, useRef, useState } from "react";
import type { PDFDocumentLoadingTask, PDFDocumentProxy, RenderTask } from "pdfjs-dist";
import type { LocalIeltsFile } from "../../modules/ielts/local-resource-access";
import type { IeltsPageRange } from "../../modules/ielts/ielts-material-manifest";

const PDF_WORKER_PATH = "/vendor/pdfjs/pdf.worker.min.mjs";

export function IeltsPdfViewer({ file, pageRange, title, compact = false }: {
  file: LocalIeltsFile | null;
  pageRange: IeltsPageRange | null;
  title: string;
  compact?: boolean;
}) {
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [sourceUrl, setSourceUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;
    let loadingTask: PDFDocumentLoadingTask | null = null;
    let loadedDocument: PDFDocumentProxy | null = null;

    if (!file) return;
    void (async () => {
      try {
        const sourceFile = await file.getFile();
        if (cancelled) return;
        objectUrl = URL.createObjectURL(sourceFile);
        setSourceUrl(objectUrl);
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = PDF_WORKER_PATH;
        loadingTask = pdfjs.getDocument({ url: objectUrl });
        loadedDocument = await loadingTask.promise;
        if (!cancelled) setDocument(loadedDocument);
      } catch (reason) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "PDF 无法读取。");
      }
    })();

    return () => {
      cancelled = true;
      void loadingTask?.destroy();
      void loadedDocument?.destroy();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [file]);

  if (!file) return <DocumentEmpty title="试题书尚未连接" copy="连接 resources 文件夹后，这里会显示所选 Test 和 Section。" />;
  if (!pageRange) return <DocumentEmpty title="这本书正在建立分页索引" copy="原始 PDF 已连接，但当前 Test / Section 暂时没有页码数据。" />;
  if (error) return <DocumentEmpty title="PDF 无法显示" copy={error} />;
  if (!document) return <DocumentEmpty title="正在打开当前 Section" copy="只加载并显示这几页，不再展示整本书。" loading />;

  const lastPage = Math.min(pageRange.endPage, document.numPages);
  const pages = Array.from({ length: Math.max(0, lastPage - pageRange.startPage + 1) }, (_, index) => pageRange.startPage + index);
  return (
    <div className={`ielts-pdf-viewer ${compact ? "compact" : ""}`}>
      <div className="ielts-pdf-toolbar">
        <div><strong>{title}</strong><span>PDF 第 {pageRange.startPage}{lastPage > pageRange.startPage ? `–${lastPage}` : ""} 页 · 共 {pages.length} 页</span></div>
        {sourceUrl && <a href={sourceUrl} target="_blank" rel="noreferrer">需要时打开整本 ↗</a>}
      </div>
      <div className="ielts-pdf-pages">
        {pages.map((pageNumber) => <PdfPage document={document} pageNumber={pageNumber} key={pageNumber} />)}
      </div>
    </div>
  );
}

function PdfPage({ document, pageNumber }: { document: PDFDocumentProxy; pageNumber: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    const wrapper = wrapperRef.current;
    if (!canvas || !wrapper) return;
    let cancelled = false;
    let renderTask: RenderTask | null = null;

    void (async () => {
      try {
        const page = await document.getPage(pageNumber);
        if (cancelled) return;
        const baseViewport = page.getViewport({ scale: 1 });
        const availableWidth = Math.min(1050, Math.max(300, wrapper.clientWidth - 32));
        const viewport = page.getViewport({ scale: availableWidth / baseViewport.width });
        const outputScale = Math.min(window.devicePixelRatio || 1, 2);
        const context = canvas.getContext("2d");
        if (!context) throw new Error("Canvas unavailable");
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;
        renderTask = page.render({
          canvas,
          canvasContext: context,
          viewport,
          transform: outputScale === 1 ? undefined : [outputScale, 0, 0, outputScale, 0, 0],
        });
        await renderTask.promise;
      } catch (reason) {
        if (!cancelled && !(reason instanceof Error && reason.name === "RenderingCancelledException")) setError(true);
      }
    })();

    return () => {
      cancelled = true;
      renderTask?.cancel();
    };
  }, [document, pageNumber]);

  return <div className="ielts-pdf-page" ref={wrapperRef}>{error ? <p>第 {pageNumber} 页无法渲染。</p> : <canvas ref={canvasRef} aria-label={`PDF 第 ${pageNumber} 页`} />}</div>;
}

function DocumentEmpty({ title, copy, loading = false }: { title: string; copy: string; loading?: boolean }) {
  return <div className="ielts-document-empty"><span className={loading ? "loading" : ""}>PDF</span><h3>{title}</h3><p>{copy}</p></div>;
}
