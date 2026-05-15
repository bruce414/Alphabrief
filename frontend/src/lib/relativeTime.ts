/** Relative time for chat timestamps (e.g. "2m", "3h"). */
export function formatRelativeTime(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  const now = Date.now();
  const sec = Math.floor((now - then) / 1000);
  if (sec < 60) return "Just now";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day}d`;
  return new Date(iso).toLocaleDateString();
}

/** "Last checked · …" line for canvas status pill. */
export function formatLastCheckedLine(
  iso: string | null,
  loading?: boolean,
): string {
  if (loading) return "Last checked · …";
  if (!iso) return "Never checked";
  const rel = formatRelativeTime(iso);
  if (rel === "Just now") return "Last checked · Just now";
  return `Last checked · ${rel} ago`;
}
