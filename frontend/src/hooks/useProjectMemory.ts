import { useCallback, useState } from "react";
import useSWR from "swr";

import { ApiError } from "@/lib/api";
import { getProjectMemory, refreshProjectMemory } from "@/lib/workspaceApi";
import type { ProjectMemory, ProjectMemoryRefreshResponse } from "@/types/workspace";

export function useProjectMemory(projectId: string | undefined) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data, mutate, isLoading } = useSWR<ProjectMemory | null>(
    projectId ? ["memory", projectId] : null,
    async () => {
      try {
        return await getProjectMemory(projectId as string);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
  );

  const refresh = useCallback(async (): Promise<ProjectMemoryRefreshResponse> => {
    if (!projectId) {
      throw new Error("No project selected");
    }
    setIsRefreshing(true);
    try {
      const result = await refreshProjectMemory(projectId);
      await mutate();
      return result;
    } finally {
      setIsRefreshing(false);
    }
  }, [projectId, mutate]);

  return { memory: data ?? null, mutate, isLoading, isRefreshing, refresh };
}
