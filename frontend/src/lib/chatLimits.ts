/**
 * Chat length policy (Alphabrief v0.3).
 *
 * - User messages: hard cap before send (hooks enforce).
 * - Assistant replies: soft display cap; full markdown remains in the API/DB.
 *   Very long threads still scroll normally; this only truncates a single
 *   assistant bubble if it exceeds the cap (protects layout/perf).
 */
export const MAX_USER_MESSAGE_CHARS = 32_000;

/** One assistant turn — markdown characters shown in the chat UI. */
export const MAX_ASSISTANT_MARKDOWN_DISPLAY_CHARS = 150_000;

export function clampAssistantMarkdownForDisplay(markdown: string): string {
  const max = MAX_ASSISTANT_MARKDOWN_DISPLAY_CHARS;
  if (markdown.length <= max) return markdown;
  return (
    markdown.slice(0, max) +
    `\n\n---\n\n*This reply was truncated for display at ${max.toLocaleString()} characters. The full text is still stored on the server.*`
  );
}
