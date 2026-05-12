import type { CSSProperties } from "react";

import { useSource } from "@/hooks/useSource";
import { T } from "@/styles/tokens";

const CHIP_HEIGHT = 24;
const CHIP_RADIUS = 8;

export function hostnameFromNormalizedUrl(url: string | null | undefined): string {
  if (!url?.trim()) return "";
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.hostname || url;
  } catch {
    return url.length > 80 ? `${url.slice(0, 77)}…` : url;
  }
}

const chipShellStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  height: CHIP_HEIGHT,
  minWidth: 0,
  maxWidth: "100%",
  padding: "0 10px",
  borderRadius: CHIP_RADIUS,
  background: T.gray100,
  color: T.gray500,
  fontFamily: T.fontSans,
  fontSize: 11,
  fontWeight: 500,
  lineHeight: 1.2,
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
  boxSizing: "border-box",
};

function SourceIdChip({ sourceId }: { sourceId: string }) {
  const { source } = useSource(sourceId);
  const label =
    (source?.title?.trim() && source.title.trim()) ||
    hostnameFromNormalizedUrl(source?.normalizedUrl ?? null) ||
    sourceId.slice(0, 8);

  return (
    <span title={label} style={chipShellStyle}>
      {label}
    </span>
  );
}

export function InlineSourceChipsRow({
  sourceIds,
  variant = "assistant",
}: {
  sourceIds: string[];
  variant?: "user" | "assistant";
}) {
  if (sourceIds.length === 0) return null;
  const isUser = variant === "user";
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 6,
        marginTop: isUser ? 6 : 12,
        maxWidth: "100%",
        ...(isUser ? { justifyContent: "flex-end" } : {}),
      }}
    >
      {sourceIds.map((id) => (
        <SourceIdChip key={id} sourceId={id} />
      ))}
    </div>
  );
}

export function UrlPreviewChips({ urls }: { urls: string[] }) {
  if (urls.length === 0) return null;
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 6,
        padding: "8px 16px 0",
      }}
    >
      {urls.map((url, i) => {
        const shown = url.length > 40 ? `${url.slice(0, 37)}…` : url;
        return (
          <span
            key={`${url}-${i}`}
            title={url}
            style={chipShellStyle}
          >
            {shown}
          </span>
        );
      })}
    </div>
  );
}
