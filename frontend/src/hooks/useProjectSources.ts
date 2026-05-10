import useSWR from "swr";

import { listProjectSources } from "@/lib/workspaceApi";

export function useProjectSources(projectId: string | undefined) {
  const { data, isLoading } = useSWR(
    projectId ? ["sources", projectId] : null,
    () => listProjectSources(projectId as string),
  );
  const sources = data?.items ?? [];
  return { sources, isLoading };
}
