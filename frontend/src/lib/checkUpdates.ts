import { apiFetch } from "./api";
import type { ProjectOverview } from "@/types/workspace";

export function runUpdateCheck(projectId: string): Promise<ProjectOverview> {
  return apiFetch(
    `/projects/${encodeURIComponent(projectId)}/overview/check-updates`,
    { method: "POST" },
  );
}
