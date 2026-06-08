import type { CSSProperties } from "react";

import { T } from "@/styles/tokens";

/** Shared floating pill chrome for canvas overlays. */
export const canvasFloatingPillStyle: CSSProperties = {
  position: "absolute",
  zIndex: 20,
  display: "flex",
  alignItems: "center",
  gap: 8,
  background: T.workspaceTopBar,
  border: `1px solid ${T.border}`,
  borderRadius: 12,
  padding: "6px 14px",
  boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
  fontFamily: T.fontSans,
  fontSize: 12,
};

export const canvasPillDividerStyle: CSSProperties = {
  width: 1,
  alignSelf: "stretch",
  minHeight: 16,
  background: T.border,
  margin: "0 8px",
  flexShrink: 0,
};
