import useSWR from "swr";

import {
  fetchPendingCandidates,
  pendingCandidatesKey,
} from "@/lib/pendingCandidates";
import type { CandidateElement } from "@/types/workspace";

export function usePendingCanvasCandidates(
  projectId: string | undefined,
  chatId: string | null | undefined,
  options?: { refreshInterval?: number },
) {
  const key = projectId ? pendingCandidatesKey(projectId, chatId) : null;

  const { data, error, isLoading, mutate, isValidating } = useSWR<
    CandidateElement[]
  >(
    key,
    () => fetchPendingCandidates(projectId!, chatId!),
    {
      refreshInterval: options?.refreshInterval ?? 0,
      revalidateOnFocus: true,
    },
  );

  return {
    pendingCandidates: data ?? [],
    pendingCount: data?.length ?? 0,
    isLoading,
    isValidating,
    error,
    mutate,
  };
}
