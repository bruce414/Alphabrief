import useSWR from "swr";

import { listProjects } from "@/lib/workspaceApi";

export function useProjects() {
  const { data, isLoading, mutate } = useSWR(["projects"], () =>
    listProjects(),
  );
  const projects = data?.items ?? [];
  const catchall = projects.find((p) => p.kind === "CATCHALL");
  return { projects, catchall, isLoading, mutate };
}
