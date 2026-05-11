import { useEffect, useMemo, useRef, useState } from "react";
import useSWR from "swr";

import { Icon } from "@/components/workspace/icons";
import { useProjects } from "@/hooks/useProjects";
import { apiFetch } from "@/lib/api";
import { T } from "@/styles/tokens";

type Canvas = {
  id: string;
  projectId: string;
  title: string;
  viewportJson: Record<string, unknown>;
  updatedAt: string;
};

type CanvasElement = {
  id: string;
  canvasId: string;
  projectId: string;
  elementType: string;
  title: string | null;
  contentMarkdown: string | null;
  contentJson: Record<string, unknown>;
  x: number;
  y: number;
  width: number | null;
  height: number | null;
  zIndex: number;
  styleJson: Record<string, unknown> | null;
  provenanceKind: string;
};

type CanvasConnection = {
  id: string;
  canvasId: string;
  fromElementId: string;
  toElementId: string;
  label: string | null;
  connectionType: string;
  styleJson: Record<string, unknown>;
};

type ListResponse<T> = { items: T[] };

function clamp(min: number, value: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

export function useCanvas(projectId: string | undefined) {
  const canvasKey = projectId ? (["canvas", projectId] as const) : null;
  const { data: canvas, mutate: mutateCanvas } = useSWR<Canvas>(
    canvasKey,
    async () => apiFetch<Canvas>(`/projects/${projectId}/canvas`),
  );

  const canvasId = canvas?.id;

  const elementsKey = canvasId
    ? (["canvasElements", canvasId] as const)
    : null;
  const connectionsKey = canvasId
    ? (["canvasConnections", canvasId] as const)
    : null;

  const { data: elementsRes, mutate: mutateElements } = useSWR<
    ListResponse<CanvasElement>
  >(elementsKey, async () =>
    apiFetch<ListResponse<CanvasElement>>(`/canvases/${canvasId}/elements`),
  );

  const { data: connectionsRes, mutate: mutateConnections } = useSWR<
    ListResponse<CanvasConnection>
  >(connectionsKey, async () =>
    apiFetch<ListResponse<CanvasConnection>>(
      `/canvases/${canvasId}/connections`,
    ),
  );

  const mutate = async () => {
    const nextCanvas = await mutateCanvas();
    const id = (nextCanvas ?? canvas)?.id;
    if (!id) return;
    await Promise.all([mutateElements(), mutateConnections()]);
  };

  return {
    canvas: canvas ?? null,
    elements: elementsRes?.items ?? [],
    connections: connectionsRes?.items ?? [],
    mutate,
  };
}

function elementTypeLabel(raw: string) {
  return raw.replace(/_/g, " ");
}

function elementBodyText(el: CanvasElement) {
  const md = el.contentMarkdown?.trim();
  const title = el.title?.trim();
  if (md) return md;
  if (title) return title;
  return "";
}

function dataDisplayValue(el: CanvasElement) {
  const v = (el.contentJson as { value?: unknown } | undefined)?.value;
  if (typeof v === "number") return String(v);
  if (typeof v === "string" && v.trim()) return v.trim();
  const fromText = elementBodyText(el);
  const m = fromText.match(/-?\d[\d,]*(?:\.\d+)?%?/);
  return m?.[0] ?? fromText;
}

export function InfiniteCanvas({ projectId }: { projectId: string }) {
  const canvasRef = useRef<HTMLDivElement | null>(null);

  const { projects } = useProjects();
  const project = useMemo(
    () => projects.find((p) => p.id === projectId) ?? null,
    [projects, projectId],
  );

  const { elements } = useCanvas(projectId);

  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(0.92);
  const [isPanning, setIsPanning] = useState(false);
  const startPanRef = useRef<{
    mouseX: number;
    mouseY: number;
    panX: number;
    panY: number;
  } | null>(null);

  const [viewport, setViewport] = useState({ w: 0, h: 0 });

  useEffect(() => {
    if (!canvasRef.current) return;
    const el = canvasRef.current;
    const ro = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (!rect) return;
      setViewport({ w: rect.width, h: rect.height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;

    const onWheel = (e: WheelEvent) => {
      // Always prevent browser/page scrolling while interacting with canvas.
      e.preventDefault();
      if (e.ctrlKey || e.metaKey) {
        setZoom((z) => clamp(0.3, z - e.deltaY * 0.002, 2));
        return;
      }
      setPan((p) => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }));
    };

    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const zoomPct = Math.round(zoom * 100);

  const worldCenter = useMemo(() => {
    const x = (viewport.w / 2 - pan.x) / zoom;
    const y = (viewport.h / 2 - pan.y) / zoom;
    return { x, y };
  }, [viewport.w, viewport.h, pan.x, pan.y, zoom]);

  return (
    <div
      ref={canvasRef}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        background: T.bg,
        backgroundImage: `radial-gradient(circle, ${T.gray300} 1px, transparent 1px)`,
        backgroundSize: `${24 * zoom}px ${24 * zoom}px`,
        backgroundPosition: `${pan.x}px ${pan.y}px`,
        fontFamily: T.fontSans,
        cursor: isPanning ? "grabbing" : "default",
        userSelect: isPanning ? "none" : "auto",
      }}
      onMouseDown={(e) => {
        const isMiddle = e.button === 1;
        const isAltDrag = e.altKey && e.button === 0;
        if (!isMiddle && !isAltDrag) return;
        e.preventDefault();
        e.stopPropagation();
        setIsPanning(true);
        startPanRef.current = {
          mouseX: e.clientX,
          mouseY: e.clientY,
          panX: pan.x,
          panY: pan.y,
        };
      }}
      onMouseMove={(e) => {
        if (!isPanning || !startPanRef.current) return;
        e.preventDefault();
        const s = startPanRef.current;
        setPan({
          x: s.panX + (e.clientX - s.mouseX),
          y: s.panY + (e.clientY - s.mouseY),
        });
      }}
      onMouseUp={() => {
        setIsPanning(false);
        startPanRef.current = null;
      }}
      onMouseLeave={() => {
        setIsPanning(false);
        startPanRef.current = null;
      }}
    >
      {/* Everything in-world transforms */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          transformOrigin: "0 0",
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          width: "100%",
          height: "100%",
        }}
      >
        <div style={{ position: "absolute", left: 60, top: 60, width: 480 }}>
          <h2
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: T.black,
              letterSpacing: "-0.02em",
              margin: 0,
              lineHeight: 1.15,
            }}
          >
            {(project?.title ?? "Project") + " — working canvas"}
          </h2>
          <p
            style={{
              fontSize: 14,
              color: T.gray400,
              lineHeight: 1.7,
              margin: "10px 0 0",
            }}
          >
            Drop quotes, charts, and screenshots here. Drag anything.
          </p>
        </div>

        {elements.length === 0 ? (
          <div
            style={{
              position: "absolute",
              left: worldCenter.x,
              top: worldCenter.y,
              transform: "translate(-50%, -50%)",
              color: T.gray400,
              fontFamily: T.fontSans,
              fontSize: 14,
              textAlign: "center",
              width: 460,
              lineHeight: 1.5,
            }}
          >
            Your canvas is empty. Add an element using the toolbar below.
          </div>
        ) : null}

        {elements.map((el) => {
          const w = el.width ?? 220;
          const h = el.height ?? undefined;
          const type = (el.elementType ?? "UNKNOWN").toUpperCase();
          const label = elementTypeLabel(type);
          const body = elementBodyText(el);
          const isQuote = type === "QUOTE";
          const isData = type === "DATA";
          return (
            <div
              key={el.id}
              style={{
                position: "absolute",
                left: el.x,
                top: el.y,
                width: w,
                height: h,
                background: T.white,
                border: `1px solid ${T.border}`,
                borderRadius: 10,
                padding: "14px 16px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                boxSizing: "border-box",
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  fontWeight: 800,
                  color: T.gray400,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  marginBottom: 10,
                }}
              >
                {label} • • • •
              </div>
              <div
                style={{
                  fontSize: isData ? 22 : 13,
                  fontWeight: isData ? 800 : 500,
                  letterSpacing: isData ? "-0.02em" : undefined,
                  lineHeight: isData ? 1.2 : 1.5,
                  color: isQuote ? T.gray600 : T.black,
                  fontStyle: isQuote ? "italic" : "normal",
                  whiteSpace: "pre-wrap",
                }}
              >
                {isData ? dataDisplayValue(el) : body}
              </div>
              <div
                style={{
                  marginTop: 12,
                  fontSize: 10,
                  fontWeight: 600,
                  color: T.gray400,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                {el.provenanceKind}
              </div>
            </div>
          );
        })}
      </div>

      {/* Zoom controls */}
      <div
        style={{
          position: "absolute",
          top: 16,
          right: 16,
          zIndex: 10,
          background: T.white,
          border: `1px solid ${T.border}`,
          borderRadius: 8,
          padding: 4,
          display: "flex",
          alignItems: "center",
          gap: 6,
          boxShadow: "0 4px 16px rgba(0,0,0,0.06)",
        }}
      >
        <button
          type="button"
          aria-label="Zoom out"
          onClick={() => setZoom((z) => clamp(0.3, z - 0.1, 2))}
          style={{
            border: "none",
            background: "transparent",
            cursor: "pointer",
            padding: "6px 8px",
            borderRadius: 6,
            color: T.black,
            fontFamily: T.fontSans,
            fontSize: 14,
            fontWeight: 700,
          }}
        >
          −
        </button>
        <span
          style={{
            fontFamily: T.fontSans,
            fontSize: 12,
            fontWeight: 700,
            color: T.black,
            minWidth: 44,
            textAlign: "center",
          }}
        >
          {zoomPct}%
        </span>
        <button
          type="button"
          aria-label="Zoom in"
          onClick={() => setZoom((z) => clamp(0.3, z + 0.1, 2))}
          style={{
            border: "none",
            background: "transparent",
            cursor: "pointer",
            padding: "6px 8px",
            borderRadius: 6,
            color: T.black,
            fontFamily: T.fontSans,
            fontSize: 14,
            fontWeight: 700,
          }}
        >
          +
        </button>
        <span style={{ color: T.gray300, padding: "0 2px" }}>|</span>
        <button
          type="button"
          onClick={() => {
            setPan({ x: 0, y: 0 });
            setZoom(0.92);
          }}
          style={{
            border: "none",
            background: "transparent",
            cursor: "pointer",
            padding: "6px 10px",
            borderRadius: 6,
            color: T.gray500,
            fontFamily: T.fontSans,
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          reset
        </button>
      </div>

      {/* Bottom toolbar */}
      <div
        style={{
          position: "absolute",
          bottom: 20,
          left: "50%",
          transform: "translateX(-50%)",
          background: T.black,
          borderRadius: 12,
          padding: "10px 16px",
          display: "flex",
          alignItems: "center",
          gap: 4,
          boxShadow: "0 4px 24px rgba(0,0,0,0.2)",
          zIndex: 10,
        }}
      >
        {[
          { key: "cursor", IconCmp: Icon.Cursor, active: true },
          { key: "move", IconCmp: Icon.Move },
          { key: "text", IconCmp: Icon.Text },
          { key: "pen", IconCmp: Icon.Pen },
          { key: "arrow", IconCmp: Icon.Arrow },
          {
            key: "image",
            IconCmp: Icon.Image,
            disabled: true,
            title: "Image upload coming soon",
          },
          { key: "note", IconCmp: Icon.Note },
          { key: "comment", IconCmp: Icon.Comment },
        ].map(({ key, IconCmp, active, disabled, title }) => (
          <button
            key={key}
            type="button"
            disabled={disabled}
            title={title}
            style={{
              border: "none",
              background: active ? "rgba(255,255,255,0.15)" : "transparent",
              color: T.white,
              padding: "7px 10px",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              cursor: disabled ? "not-allowed" : "pointer",
              opacity: disabled ? 0.55 : 1,
            }}
            onClick={() => {
              // no-op for now (creating elements comes in a later iteration)
            }}
          >
            <IconCmp width={16} height={16} />
          </button>
        ))}
      </div>
    </div>
  );
}

