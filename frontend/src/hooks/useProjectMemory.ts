import useSWR from "swr";

import { ApiError } from "@/lib/api";
import { getProjectMemory } from "@/lib/workspaceApi";
import type { ProjectMemory } from "@/types/workspace";

export function useProjectMemory(projectId: string | undefined) {
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

  return { memory: data ?? null, mutate, isLoading };
}
