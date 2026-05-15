import { useCallback, useState } from "react";

import {
  canvasFloatingPillStyle,
  canvasPillDividerStyle,
} from "@/components/workspace/canvas-pill-styles";
import { Icon } from "@/components/workspace/icons";
import { useProjectOverview } from "@/hooks/useProjectOverview";
import { runUpdateCheck } from "@/lib/checkUpdates";
import { formatLastCheckedLine } from "@/lib/relativeTime";
import { T } from "@/styles/tokens";

const UPDATES_ORANGE = "#e85d04";

export function CanvasStatusPill({ projectId }: { projectId: string }) {
  const { overview, mutate, isLoading } = useProjectOverview(projectId);
  const [isChecking, setIsChecking] = useState(false);
  const [hovered, setHovered] = useState(false);

  const updates = overview?.status.updatesAvailableCount ?? 0;
  const lastCheckedAt = overview?.status.lastCheckedAt ?? null;
  const lastCheckedLine = formatLastCheckedLine(lastCheckedAt, isLoading);

  const onCheck = useCallback(async () => {
    if (isChecking) return;
    setIsChecking(true);
    try {
      const next = await runUpdateCheck(projectId);
      await mutate(next, { revalidate: false });
    } catch (e) {
      console.error("Update check failed", e);
    } finally {
      setIsChecking(false);
    }
  }, [isChecking, mutate, projectId]);

  return (
    <button
      type="button"
      disabled={isChecking}
      onClick={() => void onCheck()}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        ...canvasFloatingPillStyle,
        bottom: 12,
        left: 12,
        border: `1px solid ${T.border}`,
        cursor: isChecking ? "wait" : "pointer",
        background: hovered && !isChecking ? T.gray100 : T.workspaceTopBar,
        transition: "background 0.15s ease",
      }}
    >
      {isChecking ? (
        <span
          aria-hidden
          style={{
            width: 14,
            height: 14,
            border: `2px solid ${T.gray300}`,
            borderTopColor: T.black,
            borderRadius: "50%",
            animation: "canvas-status-spin 0.7s linear infinite",
            flexShrink: 0,
          }}
        />
      ) : (
        <Icon.Clock width={14} height={14} style={{ color: T.gray500, flexShrink: 0 }} />
      )}
      <span style={{ fontWeight: 500, color: T.black, whiteSpace: "nowrap" }}>
        {lastCheckedLine}
      </span>
      {updates > 0 ? (
        <>
          <div style={canvasPillDividerStyle} aria-hidden />
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              fontWeight: 600,
              color: UPDATES_ORANGE,
              whiteSpace: "nowrap",
            }}
          >
            <span
              aria-hidden
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: UPDATES_ORANGE,
                flexShrink: 0,
              }}
            />
            {updates} update{updates === 1 ? "" : "s"} available
          </span>
        </>
      ) : null}
      {/* TODO Slice 4B: append "• N suggestions" segment here after updates-available, with another vertical divider */}
      <style>{`
        @keyframes canvas-status-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
}
