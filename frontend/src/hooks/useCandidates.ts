import { useCallback, useEffect, useRef, useState } from "react";

import type { CanvasElement, CandidateElement } from "@/types/workspace";
import {
  dismissCandidate,
  listCandidatesForTurn,
  promoteCandidate,
} from "@/lib/workspaceApi";

export function useCandidates(assistantTurnId: string | null | undefined) {
  const [candidates, setCandidates] = useState<CandidateElement[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const fetchedForTurnRef = useRef<string | null>(null);
  const timeoutRef = useRef<number | null>(null);

  const refetch = useCallback(async () => {
    if (!assistantTurnId) return [];
    setIsLoading(true);
    try {
      const items = await listCandidatesForTurn(assistantTurnId);
      setCandidates(items);
      return items;
    } finally {
      setIsLoading(false);
    }
  }, [assistantTurnId]);

  useEffect(() => {
    if (!assistantTurnId) return;
    if (fetchedForTurnRef.current === assistantTurnId) return;

    // Candidate extraction happens after the assistant turn completes.
    // We wait briefly so the API has time to persist the rows.
    if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    timeoutRef.current = window.setTimeout(() => {
      fetchedForTurnRef.current = assistantTurnId;
      void refetch();
    }, 500);

    return () => {
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    };
  }, [assistantTurnId, refetch]);

  const promote = useCallback(
    async (
      candidateId: string,
      body: {
        canvasId: string;
        elementType: string;
        title: string | null;
        contentMarkdown: string;
        x: number;
        y: number;
        width: number | null;
        height: number | null;
      },
    ): Promise<CanvasElement> => {
      const created = await promoteCandidate(candidateId, body);
      setCandidates((cur) =>
        cur.map((c) => (c.id === candidateId ? { ...c, status: "PROMOTED" } : c)),
      );
      return created;
    },
    [],
  );

  const dismiss = useCallback(async (candidateId: string) => {
    await dismissCandidate(candidateId);
    setCandidates((cur) => cur.filter((c) => c.id !== candidateId));
  }, []);

  return { candidates, isLoading, refetch, promote, dismiss };
}

