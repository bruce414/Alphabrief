import useSWR from "swr";

import { getProjectOverview } from "@/lib/workspaceApi";
import type { ProjectOverview } from "@/types/workspace";

export function useProjectOverview(projectId: string | undefined) {
  const { data, mutate, isLoading, error } = useSWR<ProjectOverview>(
    projectId ? ["overview", projectId] : null,
    () => getProjectOverview(projectId as string),
  );

  return {
    overview: data ?? null,
    mutate,
    isLoading,
    error,
  };
}
