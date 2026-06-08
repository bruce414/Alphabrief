import {
  useEffect,
  useRef,
  useState,
  type RefObject,
} from "react";

import type { InfiniteCanvasHandle } from "@/components/workspace/infinite-canvas";
import {
  canvasFloatingPillStyle,
  canvasPillDividerStyle,
} from "@/components/workspace/canvas-pill-styles";
import { Icon } from "@/components/workspace/icons";
import { usePendingCanvasCandidates } from "@/hooks/usePendingCanvasCandidates";
import { T } from "@/styles/tokens";

const ZOOM_STEP = 0.05;

type ViewMode = "map" | "focus" | "evidence" | "timeline" | "brief";

const VIEW_ITEMS: {
  id: ViewMode;
  label: string;
  enabled: boolean;
}[] = [
  { id: "map", label: "Map", enabled: true },
  { id: "focus", label: "Focus", enabled: false },
  { id: "evidence", label: "Evidence", enabled: false },
  { id: "timeline", label: "Timeline", enabled: false },
  { id: "brief", label: "Brief", enabled: false },
];

const zoomBtnStyle = {
  border: "none",
  background: "transparent",
  cursor: "pointer",
  padding: "2px 6px",
  borderRadius: 6,
  color: T.black,
  fontFamily: T.fontSans,
  fontSize: 14,
  fontWeight: 700,
  lineHeight: 1,
} as const;

export function CanvasViewControls({
  canvasRef,
  projectId,
  chatId,
}: {
  canvasRef: RefObject<InfiniteCanvasHandle | null>;
  projectId: string;
  chatId: string | null;
}) {
  const [viewOpen, setViewOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("map");
  const [zoomPct, setZoomPct] = useState(100);
  const [semanticZoomLevel, setSemanticZoomLevel] = useState<
    "cluster" | "node"
  >("node");
  const pillRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const { pendingCount } = usePendingCanvasCandidates(projectId, chatId, {
    refreshInterval: chatId ? 4000 : 0,
  });

  useEffect(() => {
    const handle = canvasRef.current;
    if (!handle) return;
    return handle.subscribeZoom((z) => setZoomPct(Math.round(z * 100)));
  }, [canvasRef]);

  useEffect(() => {
    const handle = canvasRef.current;
    if (!handle) return;
    return handle.subscribeSemanticZoom(setSemanticZoomLevel);
  }, [canvasRef]);

  useEffect(() => {
    if (!viewOpen) return;
    const onDocMouseDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (pillRef.current?.contains(t) || menuRef.current?.contains(t)) return;
      setViewOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setViewOpen(false);
    };
    document.addEventListener("mousedown", onDocMouseDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [viewOpen]);

  const stepZoom = (delta: number) => {
    const handle = canvasRef.current;
    if (!handle) return;
    handle.setZoom(handle.getZoom() + delta);
  };

  const currentViewLabel =
    VIEW_ITEMS.find((v) => v.id === viewMode)?.label ?? "Map";

  return (
    <div
      ref={pillRef}
      style={{
        ...canvasFloatingPillStyle,
        top: 12,
        left: 12,
      }}
    >
      <div style={{ position: "relative" }}>
        <button
          type="button"
          onClick={() => setViewOpen((o) => !o)}
          aria-expanded={viewOpen}
          aria-haspopup="listbox"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
            border: "none",
            background: "transparent",
            cursor: "pointer",
            padding: 0,
            fontFamily: T.fontSans,
            fontSize: 12,
            fontWeight: 600,
            color: T.black,
          }}
        >
          View: {currentViewLabel}
          <Icon.ChevronDown width={12} height={12} style={{ color: T.gray500 }} />
        </button>
        {viewOpen ? (
          <div
            ref={menuRef}
            role="listbox"
            style={{
              position: "absolute",
              top: "calc(100% + 6px)",
              left: 0,
              minWidth: 200,
              background: T.workspaceTopBar,
              border: `1px solid ${T.border}`,
              borderRadius: 10,
              boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
              padding: "6px 0",
              zIndex: 30,
            }}
          >
            {VIEW_ITEMS.map((item) => {
              const selected = viewMode === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  role="option"
                  aria-selected={selected}
                  disabled={!item.enabled}
                  onClick={() => {
                    if (!item.enabled) return;
                    setViewMode(item.id);
                    setViewOpen(false);
                  }}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 8,
                    padding: "8px 12px",
                    border: "none",
                    background: selected ? T.gray100 : "transparent",
                    cursor: item.enabled ? "pointer" : "not-allowed",
                    fontFamily: T.fontSans,
                    fontSize: 12,
                    fontWeight: selected ? 600 : 500,
                    color: item.enabled ? T.black : T.gray400,
                    textAlign: "left",
                  }}
                >
                  <span>{item.label}</span>
                  {item.enabled ? (
                    selected ? (
                      <span style={{ fontSize: 11, color: T.gray500 }}>✓</span>
                    ) : null
                  ) : (
                    <span
                      style={{
                        fontSize: 10,
                        fontWeight: 500,
                        color: T.gray400,
                      }}
                    >
                      Coming soon
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>

      <div style={canvasPillDividerStyle} aria-hidden />

      <button
        type="button"
        aria-label="Zoom out"
        onClick={() => stepZoom(-ZOOM_STEP)}
        style={zoomBtnStyle}
      >
        −
      </button>
      <span
        style={{
          fontFamily: T.fontSans,
          fontSize: 12,
          fontWeight: 700,
          color: T.black,
          minWidth: 36,
          textAlign: "center",
        }}
      >
        {zoomPct}%
      </span>
      <button
        type="button"
        aria-label="Zoom in"
        onClick={() => stepZoom(ZOOM_STEP)}
        style={zoomBtnStyle}
      >
        +
      </button>

      {semanticZoomLevel === "cluster" && pendingCount > 0 ? (
        <>
          <div style={canvasPillDividerStyle} aria-hidden />
          <button
            type="button"
            onClick={() => canvasRef.current?.setZoom(1)}
            style={{
              border: "none",
              background: "transparent",
              cursor: "pointer",
              padding: 0,
              fontFamily: T.fontSans,
              fontSize: 12,
              fontWeight: 600,
              color: T.black,
              whiteSpace: "nowrap",
            }}
          >
            • {pendingCount} suggestion{pendingCount === 1 ? "" : "s"}
          </button>
        </>
      ) : null}
    </div>
  );
}
