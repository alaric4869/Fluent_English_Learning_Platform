import { useEffect, useState } from "react";


export function useApiQuery<T>(loader: (signal: AbortSignal) => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    loader(controller.signal)
      .then((result) => {
        setData(result);
        setError(null);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Unable to load data.");
      });
    return () => controller.abort();
  }, [loader, revision]);

  return { data, error, refresh: () => setRevision((value) => value + 1) };
}
