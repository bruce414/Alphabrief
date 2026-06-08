import { useEffect, useState } from "react";

import { getSourceById } from "@/lib/workspaceApi";
import type { Source } from "@/types/workspace";

const sourceCache = new Map<string, Source>();
const inflight = new Map<string, Promise<Source>>();

/**
 * Fetches a single source by id with module-level caching so list renders
 * do not refetch the same id repeatedly.
 */
export function useSource(sourceId: string | null | undefined): {
  source: Source | null;
  loading: boolean;
} {
  const [source, setSource] = useState<Source | null>(() =>
    sourceId ? sourceCache.get(sourceId) ?? null : null,
  );
  const [loading, setLoading] = useState(
    () => Boolean(sourceId && !sourceCache.has(sourceId)),
  );

  useEffect(() => {
    if (!sourceId) {
      setSource(null);
      setLoading(false);
      return;
    }

    const cached = sourceCache.get(sourceId);
    if (cached) {
      setSource(cached);
      setLoading(false);
      return;
    }

    setLoading(true);
    let cancelled = false;

    const run = async () => {
      try {
        let p = inflight.get(sourceId);
        if (!p) {
          p = getSourceById(sourceId).then((s) => {
            sourceCache.set(sourceId, s);
            inflight.delete(sourceId);
            return s;
          });
          inflight.set(sourceId, p);
        }
        const s = await p;
        if (!cancelled) {
          setSource(s);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setSource(null);
          setLoading(false);
        }
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  return { source, loading };
}
