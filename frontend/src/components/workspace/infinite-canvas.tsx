import { useEffect, useId, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import useSWR from "swr";

import { Icon } from "@/components/workspace/icons";
import { useProjects } from "@/hooks/useProjects";
import { apiFetch } from "@/lib/api";
import {
  createCanvasConnection,
  deleteCanvasConnection,
  deleteCanvasElement,
  listCanvasConnections,
  patchCanvasElement,
} from "@/lib/workspaceApi";
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

const DEFAULT_ELEMENT_HEIGHT = 100;

function elementDisplayBounds(
  el: CanvasElement,
  dragPositions: Record<string, { x: number; y: number }>,
  measuredHeights: Record<string, number>,
) {
  const w = el.width ?? 220;
  const measured = measuredHeights[el.id];
  const h =
    measured ??
    (el.height != null && el.height > 0 ? el.height : DEFAULT_ELEMENT_HEIGHT);
  const drag = dragPositions[el.id];
  const x = drag?.x ?? el.x;
  const y = drag?.y ?? el.y;
  return { x, y, w, h };
}

function elementCenter(
  el: CanvasElement,
  dragPositions: Record<string, { x: number; y: number }>,
  measuredHeights: Record<string, number>,
) {
  const { x, y, w, h } = elementDisplayBounds(el, dragPositions, measuredHeights);
  return { cx: x + w / 2, cy: y + h / 2 };
}

function findElementIdAtWorldPoint(
  worldX: number,
  worldY: number,
  elements: CanvasElement[],
  dragPositions: Record<string, { x: number; y: number }>,
  measuredHeights: Record<string, number>,
): string | null {
  for (let i = elements.length - 1; i >= 0; i--) {
    const el = elements[i];
    const { x, y, w, h } = elementDisplayBounds(el, dragPositions, measuredHeights);
    if (
      worldX >= x &&
      worldX <= x + w &&
      worldY >= y &&
      worldY <= y + h
    ) {
      return el.id;
    }
  }
  return null;
}

type ListResponse<T> = { items: T[] };

function clamp(min: number, value: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

/** Canvas zoom scale: 2% … 150%. */
const ZOOM_MIN = 0.02;
const ZOOM_MAX = 1.5;
const ZOOM_DEFAULT = 1;
const ZOOM_WHEEL_STEP = 0.004;
const ZOOM_BUTTON_STEP = 0.05;

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

  const { data: connections, mutate: mutateConnections } = useSWR<
    CanvasConnection[]
  >(connectionsKey, async () => {
    if (!canvasId) return [];
    return listCanvasConnections(canvasId);
  });

  const mutate = async () => {
    const nextCanvas = await mutateCanvas();
    const id = (nextCanvas ?? canvas)?.id;
    if (!id) return;
    await Promise.all([mutateElements(), mutateConnections()]);
  };

  return {
    canvas: canvas ?? null,
    elements: elementsRes?.items ?? [],
    connections: connections ?? [],
    mutate,
    mutateConnections,
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

  const { canvas, elements, connections, mutate, mutateConnections } =
    useCanvas(projectId);
  const canvasId = canvas?.id ?? null;

  const [hoveredElementId, setHoveredElementId] = useState<string | null>(null);
  const [connectingFromId, setConnectingFromId] = useState<string | null>(null);
  const [connectPointerWorld, setConnectPointerWorld] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [selectedConnectionId, setSelectedConnectionId] = useState<
    string | null
  >(null);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(
    null,
  );
  const [deleteDialog, setDeleteDialog] = useState<
    | null
    | { kind: "block"; elementId: string }
    | { kind: "connector"; connectionId: string }
  >(null);
  const [measuredHeights, setMeasuredHeights] = useState<Record<string, number>>(
    {},
  );
  const measureObserversRef = useRef(new Map<string, ResizeObserver>());
  const measureElCallbacksRef = useRef(
    new Map<string, (node: HTMLDivElement | null) => void>(),
  );

  const getMeasureRef = (elId: string) => {
    if (!measureElCallbacksRef.current.has(elId)) {
      measureElCallbacksRef.current.set(elId, (node: HTMLDivElement | null) => {
        const prevRo = measureObserversRef.current.get(elId);
        if (prevRo) {
          prevRo.disconnect();
          measureObserversRef.current.delete(elId);
        }
        if (!node) {
          setMeasuredHeights((p) => {
            if (!(elId in p)) return p;
            const { [elId]: _, ...rest } = p;
            return rest;
          });
          return;
        }
        const ro = new ResizeObserver(() => {
          const oh = node.offsetHeight;
          setMeasuredHeights((p) => (p[elId] === oh ? p : { ...p, [elId]: oh }));
        });
        ro.observe(node);
        measureObserversRef.current.set(elId, ro);
        queueMicrotask(() => {
          const oh = node.offsetHeight;
          setMeasuredHeights((p) => (p[elId] === oh ? p : { ...p, [elId]: oh }));
        });
      });
    }
    return measureElCallbacksRef.current.get(elId)!;
  };

  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(ZOOM_DEFAULT);
  const [zoomPctDraft, setZoomPctDraft] = useState<string | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const startPanRef = useRef<{
    mouseX: number;
    mouseY: number;
    panX: number;
    panY: number;
  } | null>(null);

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const dragStartRef = useRef<{
    elementX: number;
    elementY: number;
    mouseX: number;
    mouseY: number;
  } | null>(null);
  const [dragPositions, setDragPositions] = useState<
    Record<string, { x: number; y: number }>
  >({});

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
        setZoomPctDraft(null);
        setZoom((z) =>
          clamp(ZOOM_MIN, z - e.deltaY * ZOOM_WHEEL_STEP, ZOOM_MAX),
        );
        return;
      }
      setPan((p) => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }));
    };

    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  useEffect(() => {
    if (!draggingId) return;
    const onMove = (e: MouseEvent) => {
      if (!dragStartRef.current) return;
      e.preventDefault();
      const s = dragStartRef.current;
      const dxPx = e.clientX - s.mouseX;
      const dyPx = e.clientY - s.mouseY;
      const dx = dxPx / zoom;
      const dy = dyPx / zoom;
      setDragPositions((cur) => ({
        ...cur,
        [draggingId]: { x: s.elementX + dx, y: s.elementY + dy },
      }));
    };
    const onUp = () => {
      const id = draggingId;
      const pos = dragPositions[id];
      dragStartRef.current = null;
      setDraggingId(null);
      if (!pos) return;
      void patchCanvasElement(id, { x: pos.x, y: pos.y }).then(() => mutate());
    };

    window.addEventListener("mousemove", onMove, { passive: false });
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [dragPositions, draggingId, mutate, zoom]);

  useEffect(() => {
    if (!connectingFromId) return;
    const onMove = (e: MouseEvent) => {
      e.preventDefault();
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;
      const wx = (e.clientX - rect.left - pan.x) / zoom;
      const wy = (e.clientY - rect.top - pan.y) / zoom;
      setConnectPointerWorld({ x: wx, y: wy });
    };
    const onUp = (e: MouseEvent) => {
      const rect = canvasRef.current?.getBoundingClientRect();
      const fromId = connectingFromId;
      const cid = canvasId;
      setConnectingFromId(null);
      setConnectPointerWorld(null);
      if (!rect || e.button !== 0 || !fromId || !cid) return;
      const wx = (e.clientX - rect.left - pan.x) / zoom;
      const wy = (e.clientY - rect.top - pan.y) / zoom;
      const targetId = findElementIdAtWorldPoint(
        wx,
        wy,
        elements,
        dragPositions,
        measuredHeights,
      );
      if (!targetId || targetId === fromId) return;
      void createCanvasConnection(cid, {
        fromElementId: fromId,
        toElementId: targetId,
        connectionType: "RELATED_TO",
      }).then(() => mutateConnections());
    };
    window.addEventListener("mousemove", onMove, { passive: false });
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [
    canvasId,
    connectingFromId,
    dragPositions,
    elements,
    mutateConnections,
    pan.x,
    pan.y,
    zoom,
    measuredHeights,
  ]);

  useEffect(() => {
    if (!selectedConnectionId || deleteDialog) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Backspace" && e.key !== "Delete") return;
      const t = e.target as HTMLElement | null;
      if (t?.closest?.("input, textarea, [contenteditable=true]")) return;
      e.preventDefault();
      setDeleteDialog({
        kind: "connector",
        connectionId: selectedConnectionId,
      });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedConnectionId, deleteDialog]);

  useEffect(() => {
    if (!deleteDialog) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDeleteDialog(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [deleteDialog]);

  const zoomPct = Math.round(zoom * 100);
  const zoomPctDisplay =
    zoomPctDraft !== null ? zoomPctDraft : String(zoomPct);

  function commitZoomPercentFromInput() {
    const raw = (zoomPctDraft ?? "").trim();
    const n = parseInt(raw, 10);
    if (Number.isFinite(n)) {
      setZoom(clamp(ZOOM_MIN, n / 100, ZOOM_MAX));
    }
    setZoomPctDraft(null);
  }

  const worldCenter = useMemo(() => {
    const x = (viewport.w / 2 - pan.x) / zoom;
    const y = (viewport.h / 2 - pan.y) / zoom;
    return { x, y };
  }, [viewport.w, viewport.h, pan.x, pan.y, zoom]);

  const elementById = useMemo(() => {
    const m = new Map<string, CanvasElement>();
    for (const e of elements) m.set(e.id, e);
    return m;
  }, [elements]);

  const svgMarkerPrefix = useId().replace(/:/g, "");
  const markerArrow = `conn-arrow-${svgMarkerPrefix}`;
  const markerArrowSel = `conn-arrow-sel-${svgMarkerPrefix}`;

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
        cursor: isPanning
          ? "grabbing"
          : connectingFromId
            ? "crosshair"
            : draggingId
              ? "grabbing"
              : "default",
        userSelect:
          isPanning || connectingFromId || draggingId ? "none" : "auto",
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
      <style>{`
        .canvas-md {
          font-size: 13px;
          line-height: 1.55;
          color: ${T.black};
          word-break: break-word;
        }
        .canvas-md > *:first-child { margin-top: 0; }
        .canvas-md > *:last-child { margin-bottom: 0; }
        .canvas-md p { margin: 0 0 0.75em; }
        .canvas-md strong { font-weight: 700; }
        .canvas-md em { font-style: italic; }
        .canvas-md a {
          color: ${T.black};
          text-decoration: underline;
          text-underline-offset: 2px;
        }
        .canvas-md code {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          font-size: 0.92em;
          background: ${T.gray100};
          border: 1px solid ${T.border};
          border-radius: 4px;
          padding: 1px 5px;
        }
        .canvas-md pre {
          margin: 0.6em 0 0.85em;
          padding: 12px 14px;
          background: ${T.gray100};
          border: 1px solid ${T.border};
          border-radius: 8px;
          overflow-x: auto;
          line-height: 1.55;
        }
        .canvas-md pre code {
          background: transparent;
          border: none;
          padding: 0;
          font-size: 12px;
        }
        .canvas-md blockquote {
          margin: 0.6em 0 0.85em;
          padding: 0.2em 0 0.2em 12px;
          border-left: 3px solid ${T.gray200};
          color: ${T.gray600};
        }
        .canvas-md ul,
        .canvas-md ol {
          margin: 0 0 0.85em;
          padding-left: 1.2em;
        }
        .canvas-md li { margin: 0.2em 0; }
      `}</style>

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
        onMouseDown={(e) => {
          if (e.currentTarget === e.target) {
            setSelectedConnectionId(null);
            setSelectedElementId(null);
          }
        }}
      >
        <svg
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) {
              setSelectedConnectionId(null);
              setSelectedElementId(null);
            }
          }}
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            width: "100%",
            height: "100%",
            zIndex: 0,
            overflow: "visible",
          }}
        >
          <defs>
            <marker
              id={markerArrow}
              markerWidth="7"
              markerHeight="7"
              refX="6"
              refY="3.5"
              orient="auto"
              markerUnits="userSpaceOnUse"
            >
              <polygon points="0 0, 7 3.5, 0 7" fill={T.gray400} />
            </marker>
            <marker
              id={markerArrowSel}
              markerWidth="7"
              markerHeight="7"
              refX="6"
              refY="3.5"
              orient="auto"
              markerUnits="userSpaceOnUse"
            >
              <polygon points="0 0, 7 3.5, 0 7" fill={T.black} />
            </marker>
          </defs>
          {connections.map((c) => {
            const from = elementById.get(c.fromElementId);
            const to = elementById.get(c.toElementId);
            if (!from || !to) return null;
            const a = elementCenter(from, dragPositions, measuredHeights);
            const b = elementCenter(to, dragPositions, measuredHeights);
            const sel = selectedConnectionId === c.id;
            return (
              <g key={c.id}>
                <line
                  x1={a.cx}
                  y1={a.cy}
                  x2={b.cx}
                  y2={b.cy}
                  stroke="transparent"
                  strokeWidth={14}
                  style={{ pointerEvents: "stroke", cursor: "pointer" }}
                  onMouseDown={(e) => {
                    e.stopPropagation();
                    setSelectedElementId(null);
                    setSelectedConnectionId(c.id);
                  }}
                  onDoubleClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setDeleteDialog({
                      kind: "connector",
                      connectionId: c.id,
                    });
                  }}
                />
                <line
                  x1={a.cx}
                  y1={a.cy}
                  x2={b.cx}
                  y2={b.cy}
                  stroke={sel ? T.black : T.gray400}
                  strokeWidth={sel ? 3 : 1.5}
                  fill="none"
                  markerEnd={
                    sel ? `url(#${markerArrowSel})` : `url(#${markerArrow})`
                  }
                  style={{ pointerEvents: "none" }}
                />
              </g>
            );
          })}
          {connectingFromId && connectPointerWorld
            ? (() => {
                const from = elementById.get(connectingFromId);
                if (!from) return null;
                const { cx, cy } = elementCenter(
                  from,
                  dragPositions,
                  measuredHeights,
                );
                const { x: px, y: py } = connectPointerWorld;
                return (
                  <line
                    x1={cx}
                    y1={cy}
                    x2={px}
                    y2={py}
                    stroke={T.gray400}
                    strokeWidth={1.5}
                    strokeDasharray="5 5"
                    fill="none"
                  />
                );
              })()
            : null}
        </svg>

        <div
          style={{ position: "absolute", left: 60, top: 128, width: 480, zIndex: 1 }}
        >
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
              zIndex: 1,
            }}
          >
            Your canvas is empty. Add an element using the toolbar below.
          </div>
        ) : null}

        {elements.map((el) => {
          const w = el.width ?? 220;
          const minH =
            el.height != null && el.height > 0 ? el.height : undefined;
          const type = (el.elementType ?? "UNKNOWN").toUpperCase();
          const label = elementTypeLabel(type);
          const body = elementBodyText(el);
          const isQuote = type === "QUOTE";
          const isData = type === "DATA";
          const dragPos = dragPositions[el.id];
          const x = dragPos?.x ?? el.x;
          const y = dragPos?.y ?? el.y;
          return (
            <div
              key={el.id}
              ref={getMeasureRef(el.id)}
              onMouseEnter={() => setHoveredElementId(el.id)}
              onMouseLeave={() =>
                setHoveredElementId((cur) => (cur === el.id ? null : cur))
              }
              style={{
                position: "absolute",
                left: x,
                top: y,
                width: w,
                minHeight: minH,
                background: T.white,
                border: `1px solid ${T.border}`,
                borderRadius: 10,
                padding: "14px 16px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                boxSizing: "border-box",
                cursor: draggingId === el.id ? "grabbing" : "grab",
                zIndex: selectedElementId === el.id ? 2 : 1,
              }}
              onMouseDown={(e) => {
                if (e.button !== 0) return;
                if (e.altKey) return;
                if (connectingFromId) return;
                e.preventDefault();
                e.stopPropagation();
                setSelectedConnectionId(null);
                setSelectedElementId(el.id);
                setDraggingId(el.id);
                dragStartRef.current = {
                  elementX: x,
                  elementY: y,
                  mouseX: e.clientX,
                  mouseY: e.clientY,
                };
              }}
            >
              {selectedElementId === el.id ? (
                <button
                  type="button"
                  aria-label="Remove block"
                  onMouseDown={(e) => e.stopPropagation()}
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteDialog({ kind: "block", elementId: el.id });
                  }}
                  style={{
                    position: "absolute",
                    top: 8,
                    right: 8,
                    zIndex: 4,
                    width: 28,
                    height: 28,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    borderRadius: 6,
                    border: `1px solid ${T.border}`,
                    background: T.white,
                    cursor: "pointer",
                    padding: 0,
                    color: T.gray600,
                  }}
                >
                  <Icon.Trash width={14} height={14} />
                </button>
              ) : null}
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
                  whiteSpace: isData ? "pre-wrap" : undefined,
                }}
              >
                {isData ? (
                  dataDisplayValue(el)
                ) : (
                  <div className="canvas-md" style={{ color: isQuote ? T.gray600 : T.black }}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeSanitize]}
                    >
                      {body}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
              <div
                style={{
                  marginTop: 12,
                  fontSize: 10,
                  fontWeight: 600,
                  color: T.gray400,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  paddingBottom: 2,
                }}
              >
                {el.provenanceKind}
              </div>
              <div
                role="presentation"
                aria-hidden
                onMouseDown={(e) => {
                  if (e.button !== 0) return;
                  e.preventDefault();
                  e.stopPropagation();
                  const rect = canvasRef.current?.getBoundingClientRect();
                  if (!rect) return;
                  const wx = (e.clientX - rect.left - pan.x) / zoom;
                  const wy = (e.clientY - rect.top - pan.y) / zoom;
                  setConnectingFromId(el.id);
                  setConnectPointerWorld({ x: wx, y: wy });
                }}
                style={{
                  position: "absolute",
                  right: -4,
                  top: "50%",
                  width: 8,
                  height: 8,
                  marginTop: -4,
                  borderRadius: 4,
                  background: T.black,
                  boxSizing: "border-box",
                  zIndex: 2,
                  opacity: hoveredElementId === el.id ? 1 : 0,
                  pointerEvents:
                    hoveredElementId === el.id ? "auto" : "none",
                  cursor: "crosshair",
                }}
              />
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
          onClick={() => {
            setZoomPctDraft(null);
            setZoom((z) =>
              clamp(ZOOM_MIN, z - ZOOM_BUTTON_STEP, ZOOM_MAX),
            );
          }}
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
        <input
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          title="Zoom 2–150%"
          aria-label="Zoom percent (2 to 150)"
          value={zoomPctDisplay}
          onChange={(e) => setZoomPctDraft(e.target.value)}
          onFocus={() => setZoomPctDraft(String(zoomPct))}
          onBlur={() => commitZoomPercentFromInput()}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              commitZoomPercentFromInput();
              (e.target as HTMLInputElement).blur();
            }
            if (e.key === "Escape") {
              setZoomPctDraft(null);
              (e.target as HTMLInputElement).blur();
            }
          }}
          style={{
            fontFamily: T.fontSans,
            fontSize: 12,
            fontWeight: 700,
            color: T.black,
            width: 50,
            textAlign: "center",
            border: "none",
            background: "transparent",
            padding: "4px 2px",
            outline: "none",
            borderRadius: 4,
          }}
        />
        <span
          style={{
            fontFamily: T.fontSans,
            fontSize: 11,
            fontWeight: 600,
            color: T.gray500,
            marginLeft: -4,
            marginRight: 2,
          }}
        >
          %
        </span>
        <button
          type="button"
          aria-label="Zoom in"
          onClick={() => {
            setZoomPctDraft(null);
            setZoom((z) =>
              clamp(ZOOM_MIN, z + ZOOM_BUTTON_STEP, ZOOM_MAX),
            );
          }}
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
            setZoom(ZOOM_DEFAULT);
            setZoomPctDraft(null);
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

      {deleteDialog ? (
        <div
          role="presentation"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 2000,
            padding: 24,
          }}
          onClick={() => setDeleteDialog(null)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-canvas-dialog-title"
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "100%",
              maxWidth: 420,
              background: T.white,
              borderRadius: 16,
              padding: 32,
              boxShadow: "0 12px 40px rgba(0,0,0,0.12)",
              fontFamily: T.fontSans,
            }}
          >
            <h2
              id="delete-canvas-dialog-title"
              style={{
                fontSize: 18,
                fontWeight: 700,
                color: T.black,
                marginBottom: 12,
              }}
            >
              {deleteDialog.kind === "block"
                ? "Remove block?"
                : "Remove connector?"}
            </h2>
            <p
              style={{
                fontSize: 14,
                lineHeight: 1.55,
                color: T.gray600,
                margin: "0 0 24px",
              }}
            >
              {deleteDialog.kind === "block"
                ? "Do you want to remove this block?"
                : "Do you want to remove this connector?"}
            </p>
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 10,
              }}
            >
              <button
                type="button"
                onClick={() => setDeleteDialog(null)}
                style={{
                  padding: "8px 16px",
                  borderRadius: 8,
                  border: `1px solid ${T.border}`,
                  background: T.white,
                  cursor: "pointer",
                  fontFamily: T.fontSans,
                  fontSize: 13,
                  fontWeight: 500,
                  color: T.black,
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  if (deleteDialog.kind === "block") {
                    const id = deleteDialog.elementId;
                    void deleteCanvasElement(id).then(() => {
                      setSelectedElementId((cur) =>
                        cur === id ? null : cur,
                      );
                      setMeasuredHeights((p) => {
                        if (!(id in p)) return p;
                        const { [id]: _, ...rest } = p;
                        return rest;
                      });
                      setDeleteDialog(null);
                      void mutate();
                    });
                  } else {
                    const cid = deleteDialog.connectionId;
                    void deleteCanvasConnection(cid).then(() => {
                      setSelectedConnectionId((cur) =>
                        cur === cid ? null : cur,
                      );
                      setDeleteDialog(null);
                      void mutateConnections();
                    });
                  }
                }}
                style={{
                  padding: "8px 16px",
                  borderRadius: 8,
                  border: "1px solid #fecdca",
                  background: "#fef3f2",
                  cursor: "pointer",
                  fontFamily: T.fontSans,
                  fontSize: 13,
                  fontWeight: 600,
                  color: "#b42318",
                }}
              >
                {deleteDialog.kind === "block"
                  ? "Remove block"
                  : "Remove connector"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

