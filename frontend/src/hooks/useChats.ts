import useSWR from "swr";

import { listChats } from "@/lib/workspaceApi";

export function useChats(projectId: string | undefined) {
  const { data, isLoading } = useSWR(
    projectId ? ["chats", projectId] : null,
    () => listChats(projectId as string),
  );
  const chats = data?.items ?? [];
  return { chats, isLoading };
}
