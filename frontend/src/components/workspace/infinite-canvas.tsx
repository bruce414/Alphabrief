import type {
  CSSProperties,
  MouseEventHandler,
  ReactNode,
} from "react";
import {
  forwardRef,
  useCallback,
  useEffect,
  useId,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import { flushSync } from "react-dom";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import useSWR from "swr";

import { CandidateGhostLayer } from "@/components/workspace/canvas-ghost-layer";
import { Icon } from "@/components/workspace/icons";
import { useProjects } from "@/hooks/useProjects";
import { apiFetch } from "@/lib/api";
import {
  createCanvasConnection,
  createManualElement,
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

function layoutDimensions(
  el: CanvasElement,
  type: string,
): { w: number; h?: number } {
  switch (type) {
    case "MINDMAP_NODE":
      return { w: el.width ?? 160, h: el.height ?? 72 };
    case "GROUP":
      return { w: el.width ?? 360, h: el.height ?? 240 };
    case "DIRECTION":
      return { w: el.width ?? 280, h: el.height ?? 100 };
    case "TEXT":
    case "STICKY_NOTE":
      return { w: el.width ?? 240, h: el.height ?? 140 };
    default:
      return { w: el.width ?? 220, h: undefined };
  }
}

function isClusterZoomAnchorType(type: string): boolean {
  return type === "GROUP" || type === "DIRECTION";
}

const DEFAULT_ELEMENT_HEIGHT = 100;

function elementDisplayBounds(
  el: CanvasElement,
  dragPositions: Record<string, { x: number; y: number }>,
  measuredHeights: Record<string, number>,
) {
  const type = (el.elementType ?? "TEXT").toUpperCase();
  const dims = layoutDimensions(el, type);
  const w = dims.w;
  const measured = measuredHeights[el.id];
  const fallbackH = dims.h ?? DEFAULT_ELEMENT_HEIGHT;
  const h =
    measured ??
    (el.height != null && el.height > 0 ? el.height : fallbackH);
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

const SEMANTIC_CLUSTER_TO_NODE = 0.65;
const SEMANTIC_NODE_TO_CLUSTER = 0.55;

type SemanticZoomLevel = "cluster" | "node";

function countNodesInGroup(
  group: CanvasElement,
  elements: CanvasElement[],
  dragPositions: Record<string, { x: number; y: number }>,
  measuredHeights: Record<string, number>,
): number {
  const bounds = elementDisplayBounds(group, dragPositions, measuredHeights);
  let n = 0;
  for (const el of elements) {
    const type = (el.elementType ?? "TEXT").toUpperCase();
    if (type === "GROUP" || type === "DIRECTION") continue;
    const { cx, cy } = elementCenter(el, dragPositions, measuredHeights);
    if (
      cx >= bounds.x &&
      cx <= bounds.x + bounds.w &&
      cy >= bounds.y &&
      cy <= bounds.y + bounds.h
    ) {
      n += 1;
    }
  }
  return n;
}

export function useCanvas(projectId: string | undefined) {
  const canvasKey = projectId ? (["canvas", projectId] as const) : null;
  const {
    data: canvas,
    mutate: mutateCanvas,
    isLoading: isCanvasLoading,
  } = useSWR<Canvas>(
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

  const { data: elementsRes, mutate: mutateElements, isLoading: isElementsLoading } =
    useSWR<ListResponse<CanvasElement>>(elementsKey, async () =>
      apiFetch<ListResponse<CanvasElement>>(`/canvases/${canvasId}/elements`),
    );

  const {
    data: connections,
    mutate: mutateConnections,
    isLoading: isConnectionsLoading,
  } = useSWR<CanvasConnection[]>(connectionsKey, async () => {
    if (!canvasId) return [];
    return listCanvasConnections(canvasId);
  });

  const mutate = async () => {
    const nextCanvas = await mutateCanvas();
    const id = (nextCanvas ?? canvas)?.id;
    if (!id) return;
    await Promise.all([mutateElements(), mutateConnections()]);
  };

  const isLoading =
    Boolean(projectId) &&
    (isCanvasLoading ||
      (Boolean(canvasId) && (isElementsLoading || isConnectionsLoading)));

  return {
    canvas: canvas ?? null,
    elements: elementsRes?.items ?? [],
    connections: connections ?? [],
    isLoading,
    mutate,
    mutateConnections,
  };
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

function imageUrlFromJson(el: CanvasElement): string | null {
  const raw = (el.contentJson as { imageUrl?: unknown } | undefined)?.imageUrl;
  return typeof raw === "string" && raw.trim() ? raw.trim() : null;
}

function TypeBadge({
  children,
  color = T.black,
  bg = T.gray100,
}: {
  children: ReactNode;
  color?: string;
  bg?: string;
}) {
  return (
    <div
      style={{
        alignSelf: "flex-start",
        fontSize: 9,
        fontWeight: 800,
        color,
        background: bg,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        padding: "3px 7px",
        borderRadius: 4,
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  );
}

function ProvenanceFooter({ kind }: { kind: string }) {
  return (
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
      {kind}
    </div>
  );
}

const CREATION_TYPES = [
  {
    elementType: "TEXT",
    label: "Text",
    w: 240,
    h: 140,
    title: null as string | null,
  },
  {
    elementType: "STICKY_NOTE",
    label: "Sticky note",
    w: 240,
    h: 140,
    title: null as string | null,
  },
  {
    elementType: "MINDMAP_NODE",
    label: "Mindmap node",
    w: 160,
    h: 72,
    title: "Topic",
  },
  {
    elementType: "GROUP",
    label: "Group",
    w: 360,
    h: 240,
    title: "Group",
  },
] as const;

export type CanvasQuickCreateKind = (typeof CREATION_TYPES)[number]["elementType"];

export type InfiniteCanvasHandle = {
  createElement: (kind: CanvasQuickCreateKind) => void;
  getZoom: () => number;
  setZoom: (z: number) => void;
  subscribeZoom: (cb: (z: number) => void) => () => void;
  getSemanticZoomLevel: () => SemanticZoomLevel;
  subscribeSemanticZoom: (cb: (level: SemanticZoomLevel) => void) => () => void;
};

const CREATION_BY_KIND = new Map<CanvasQuickCreateKind, (typeof CREATION_TYPES)[number]>(
  CREATION_TYPES.map((s) => [s.elementType, s]),
);

export const InfiniteCanvas = forwardRef<
  InfiniteCanvasHandle,
  { projectId: string; chatId?: string | null }
>(function InfiniteCanvas({ projectId, chatId = null }, forwardedRef) {
  const canvasRef = useRef<HTMLDivElement | null>(null);

  const { projects } = useProjects();
  const project = useMemo(
    () => projects.find((p) => p.id === projectId) ?? null,
    [projects, projectId],
  );

  const { canvas, elements, connections, mutate, mutateConnections } =
    useCanvas(projectId);
  const canvasId = canvas?.id ?? null;

  const [pendingRemovedElementIds, setPendingRemovedElementIds] = useState<
    Record<string, true>
  >({});
  const [pendingRemovedConnectionIds, setPendingRemovedConnectionIds] =
    useState<Record<string, true>>({});

  useEffect(() => {
    setPendingRemovedElementIds({});
    setPendingRemovedConnectionIds({});
  }, [canvasId]);

  const displayElements = useMemo(
    () => elements.filter((e) => !pendingRemovedElementIds[e.id]),
    [elements, pendingRemovedElementIds],
  );
  const displayConnections = useMemo(
    () => connections.filter((c) => !pendingRemovedConnectionIds[c.id]),
    [connections, pendingRemovedConnectionIds],
  );

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
  const [zoom, setZoomState] = useState(ZOOM_DEFAULT);
  const [semanticZoomLevel, setSemanticZoomLevel] =
    useState<SemanticZoomLevel>("node");
  const zoomRef = useRef(zoom);
  zoomRef.current = zoom;
  const zoomListenersRef = useRef(new Set<(z: number) => void>());
  const semanticZoomRef = useRef(semanticZoomLevel);
  semanticZoomRef.current = semanticZoomLevel;
  const semanticZoomListenersRef = useRef(
    new Set<(level: SemanticZoomLevel) => void>(),
  );
  const [isPanning, setIsPanning] = useState(false);

  const setZoom = useCallback((next: number | ((z: number) => number)) => {
    setZoomState((z) => {
      const resolved = typeof next === "function" ? next(z) : next;
      return clamp(ZOOM_MIN, resolved, ZOOM_MAX);
    });
  }, []);

  useEffect(() => {
    zoomListenersRef.current.forEach((cb) => cb(zoom));
  }, [zoom]);

  useEffect(() => {
    semanticZoomListenersRef.current.forEach((cb) =>
      cb(semanticZoomLevel),
    );
  }, [semanticZoomLevel]);

  useEffect(() => {
    setSemanticZoomLevel((prev) => {
      if (prev === "cluster" && zoom > SEMANTIC_CLUSTER_TO_NODE) return "node";
      if (prev === "node" && zoom < SEMANTIC_NODE_TO_CLUSTER) return "cluster";
      return prev;
    });
  }, [zoom]);

  const visibleElements = useMemo(() => {
    if (semanticZoomLevel === "node") return displayElements;
    return displayElements.filter((e) =>
      isClusterZoomAnchorType((e.elementType ?? "TEXT").toUpperCase()),
    );
  }, [displayElements, semanticZoomLevel]);

  const visibleElementIds = useMemo(
    () => new Set(visibleElements.map((e) => e.id)),
    [visibleElements],
  );

  const visibleConnections = useMemo(
    () =>
      displayConnections.filter(
        (c) =>
          visibleElementIds.has(c.fromElementId) &&
          visibleElementIds.has(c.toElementId),
      ),
    [displayConnections, visibleElementIds],
  );

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
  const dragPositionsRef = useRef(dragPositions);
  dragPositionsRef.current = dragPositions;

  const [viewport, setViewport] = useState({ w: 0, h: 0 });
  const [isCreatingElement, setIsCreatingElement] = useState(false);

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
        setZoom((z) => z - e.deltaY * ZOOM_WHEEL_STEP);
        return;
      }
      setPan((p) => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }));
    };

    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  useEffect(() => {
    if (!draggingId) return;
    const idCapture = draggingId;
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
        [idCapture]: { x: s.elementX + dx, y: s.elementY + dy },
      }));
    };
    const onUp = () => {
      const pos = dragPositionsRef.current[idCapture];
      dragStartRef.current = null;
      setDraggingId(null);
      if (!pos) return;
      void patchCanvasElement(idCapture, { x: pos.x, y: pos.y }).then(() =>
        mutate(),
      );
    };

    window.addEventListener("mousemove", onMove, { passive: false });
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [draggingId, mutate, zoom]);

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
        visibleElements,
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
    visibleElements,
    dragPositions,
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

  const worldCenter = useMemo(() => {
    const x = (viewport.w / 2 - pan.x) / zoom;
    const y = (viewport.h / 2 - pan.y) / zoom;
    return { x, y };
  }, [viewport.w, viewport.h, pan.x, pan.y, zoom]);

  const onCreateElement = useCallback(
    async (spec: (typeof CREATION_TYPES)[number]) => {
      if (!canvasId || isCreatingElement) return;
      setIsCreatingElement(true);
      try {
        const x = worldCenter.x - spec.w / 2;
        const y = worldCenter.y - spec.h / 2;
        await createManualElement(canvasId, {
          elementType: spec.elementType,
          title: spec.title,
          contentMarkdown: spec.elementType === "MINDMAP_NODE" ? null : "",
          contentJson: {},
          x,
          y,
          width: spec.w,
          height: spec.h,
        });
        await mutate();
      } catch (e) {
        console.error("Failed to create canvas element", e);
      } finally {
        setIsCreatingElement(false);
      }
    },
    [canvasId, isCreatingElement, worldCenter.x, worldCenter.y, mutate],
  );

  useImperativeHandle(
    forwardedRef,
    () => ({
      createElement(kind: CanvasQuickCreateKind) {
        const spec = CREATION_BY_KIND.get(kind);
        if (spec) void onCreateElement(spec);
      },
      getZoom: () => zoomRef.current,
      setZoom: (z: number) => setZoom(z),
      subscribeZoom(cb: (z: number) => void) {
        zoomListenersRef.current.add(cb);
        cb(zoomRef.current);
        return () => {
          zoomListenersRef.current.delete(cb);
        };
      },
      getSemanticZoomLevel: () => semanticZoomRef.current,
      subscribeSemanticZoom(cb: (level: SemanticZoomLevel) => void) {
        semanticZoomListenersRef.current.add(cb);
        cb(semanticZoomRef.current);
        return () => {
          semanticZoomListenersRef.current.delete(cb);
        };
      },
    }),
    [onCreateElement, setZoom],
  );

  const elementById = useMemo(() => {
    const m = new Map<string, CanvasElement>();
    for (const e of visibleElements) m.set(e.id, e);
    return m;
  }, [visibleElements]);

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
          {visibleConnections.map((c) => {
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

        {visibleElements.length === 0 ? (
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
            Your canvas is empty. Add an element using the toolbar above.
          </div>
        ) : null}

        {canvasId && chatId ? (
          <CandidateGhostLayer
            projectId={projectId}
            chatId={chatId}
            canvasId={canvasId}
            semanticZoomLevel={semanticZoomLevel}
            pan={pan}
            zoom={zoom}
            viewport={viewport}
          />
        ) : null}

        {visibleElements.map((el) => {
          const type = (el.elementType ?? "TEXT").toUpperCase();
          const dims = layoutDimensions(el, type);
          const w = dims.w;
          const minH =
            el.height != null && el.height > 0 ? el.height : dims.h;
          const body = elementBodyText(el);
          const dragPos = dragPositions[el.id];
          const x = dragPos?.x ?? el.x;
          const y = dragPos?.y ?? el.y;

          const isData = type === "DATA";
          const isQuestion = type === "QUESTION";
          const isAi = type === "AI_BLOCK";
          const sticky = type === "STICKY_NOTE";
          const isRisk = type === "RISK";

          const badge =
            type === "CLAIM" ? (
              <TypeBadge>Claim</TypeBadge>
            ) : type === "EVIDENCE" ? (
              <TypeBadge>Evidence</TypeBadge>
            ) : type === "DATA" ? (
              <TypeBadge color={T.gray500} bg={T.gray200}>
                Data
              </TypeBadge>
            ) : type === "QUESTION" ? (
              <TypeBadge color={T.white} bg={T.black}>
                ?
              </TypeBadge>
            ) : type === "RISK" ? (
              <TypeBadge color={T.red500} bg={`${T.red500}22`}>
                Risk
              </TypeBadge>
            ) : type === "CATALYST" ? (
              <TypeBadge>Catalyst</TypeBadge>
            ) : null;

          const showProvenance = ![
            "QUOTE",
            "MINDMAP_NODE",
            "GROUP",
            "DIRECTION",
            "IMAGE",
          ].includes(type);

          const innerBodyStyle: CSSProperties = {
            fontSize: isData ? 15 : 13,
            fontWeight: isData ? 700 : isQuestion ? 700 : 500,
            letterSpacing: isData ? "-0.02em" : undefined,
            lineHeight: 1.5,
            color: T.black,
            fontStyle: "normal",
            whiteSpace: "pre-wrap",
            fontFamily: isData ? T.fontMono : T.fontSans,
          };

          const trashBtn =
            selectedElementId === el.id ? (
              <button
                type="button"
                aria-label="Remove block"
                onMouseDown={(e) => e.stopPropagation()}
                onClick={(e) => {
                  e.stopPropagation();
                  setDraggingId(null);
                  dragStartRef.current = null;
                  setDragPositions((p) => {
                    if (!(el.id in p)) return p;
                    const { [el.id]: _, ...rest } = p;
                    return rest;
                  });
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
            ) : null;

          const connectorHandle = (
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
          );

          let outerStyle: CSSProperties = {
            position: "absolute",
            left: x,
            top: y,
            width: w,
            minHeight: minH,
            boxSizing: "border-box",
            cursor: draggingId === el.id ? "grabbing" : "grab",
            zIndex: selectedElementId === el.id ? 2 : 1,
            background: T.white,
            border: `1px solid ${T.border}`,
            borderRadius: 10,
            padding: "14px 16px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
            display: "flex",
            flexDirection: "column",
          };

          if (type === "QUOTE") {
            outerStyle = {
              ...outerStyle,
              background: "transparent",
              border: "none",
              padding: "4px 0 4px 14px",
              borderRadius: 0,
              boxShadow: "none",
              borderLeft: `3px solid ${T.gray300}`,
            };
          } else if (sticky) {
            outerStyle = {
              ...outerStyle,
              background: "#fff8c5",
              border: "none",
              borderRadius: 6,
              boxShadow: "0 3px 10px rgba(0,0,0,0.12)",
            };
          } else if (type === "MINDMAP_NODE") {
            outerStyle = {
              ...outerStyle,
              alignItems: "center",
              justifyContent: "center",
              borderRadius: 32,
              padding: "8px 14px",
              fontSize: 13,
              fontWeight: 600,
              textAlign: "center",
            };
          } else if (type === "GROUP") {
            outerStyle = {
              ...outerStyle,
              background: "transparent",
              border: `2px dashed ${T.gray300}`,
              padding: 0,
              overflow: "hidden",
            };
          } else if (isRisk) {
            outerStyle = {
              ...outerStyle,
              boxShadow: `0 2px 8px rgba(0,0,0,0.06), inset 3px 0 0 0 ${T.red500}`,
            };
          }

          const onCardMouseDown: MouseEventHandler<HTMLDivElement> = (e) => {
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
          };

          if (type === "QUOTE") {
            return (
              <div
                key={el.id}
                ref={getMeasureRef(el.id)}
                onMouseEnter={() => setHoveredElementId(el.id)}
                onMouseLeave={() =>
                  setHoveredElementId((cur) => (cur === el.id ? null : cur))
                }
                style={outerStyle}
                onMouseDown={onCardMouseDown}
              >
                {trashBtn}
                <div
                  className="canvas-md"
                  style={{
                    fontFamily: T.fontSans,
                    fontSize: 13,
                    fontStyle: "italic",
                    color: T.gray600,
                  }}
                >
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeSanitize]}
                  >
                    {body || "—"}
                  </ReactMarkdown>
                </div>
                {connectorHandle}
              </div>
            );
          }

          if (type === "DIRECTION") {
            const directionTitle = el.title?.trim() || "Research direction";
            const directionOuterStyle: CSSProperties = {
              position: "absolute",
              left: x,
              top: y,
              width: w,
              minHeight: minH,
              boxSizing: "border-box",
              cursor: draggingId === el.id ? "grabbing" : "grab",
              zIndex: selectedElementId === el.id ? 2 : 1,
              background: T.black,
              border: "none",
              borderRadius: 999,
              padding: "14px 20px 16px",
              boxShadow: "0 6px 24px rgba(0,0,0,0.12)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
              fontFamily: T.fontSans,
            };
            const directionConnectorHandle = (
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
                  background: T.white,
                  boxSizing: "border-box",
                  zIndex: 2,
                  opacity: hoveredElementId === el.id ? 1 : 0,
                  pointerEvents:
                    hoveredElementId === el.id ? "auto" : "none",
                  cursor: "crosshair",
                }}
              />
            );
            return (
              <div
                key={el.id}
                ref={getMeasureRef(el.id)}
                onMouseEnter={() => setHoveredElementId(el.id)}
                onMouseLeave={() =>
                  setHoveredElementId((cur) => (cur === el.id ? null : cur))
                }
                style={directionOuterStyle}
                onMouseDown={onCardMouseDown}
              >
                {trashBtn}
                <div
                  style={{
                    fontSize: 9,
                    fontWeight: 700,
                    color: T.gray400,
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    marginBottom: 6,
                    lineHeight: 1.2,
                  }}
                >
                  DIRECTION
                </div>
                <div
                  style={{
                    fontSize: 17,
                    fontWeight: 700,
                    color: T.white,
                    lineHeight: 1.25,
                    wordBreak: "break-word",
                  }}
                >
                  {directionTitle}
                </div>
                {directionConnectorHandle}
              </div>
            );
          }

          if (type === "MINDMAP_NODE") {
            const labelText = (el.title?.trim() || body || "Node").slice(
              0,
              80,
            );
            return (
              <div
                key={el.id}
                ref={getMeasureRef(el.id)}
                onMouseEnter={() => setHoveredElementId(el.id)}
                onMouseLeave={() =>
                  setHoveredElementId((cur) => (cur === el.id ? null : cur))
                }
                style={outerStyle}
                onMouseDown={onCardMouseDown}
              >
                {trashBtn}
                <span style={{ color: T.black }}>{labelText}</span>
                {connectorHandle}
              </div>
            );
          }

          if (type === "GROUP") {
            const title = el.title?.trim() || "Group";
            const nodeCount =
              semanticZoomLevel === "cluster"
                ? countNodesInGroup(
                    el,
                    displayElements,
                    dragPositions,
                    measuredHeights,
                  )
                : 0;
            return (
              <div
                key={el.id}
                ref={getMeasureRef(el.id)}
                onMouseEnter={() => setHoveredElementId(el.id)}
                onMouseLeave={() =>
                  setHoveredElementId((cur) => (cur === el.id ? null : cur))
                }
                style={{
                  ...outerStyle,
                  display: "flex",
                  flexDirection: "column",
                  position: "relative",
                }}
                onMouseDown={onCardMouseDown}
              >
                {trashBtn}
                {semanticZoomLevel === "cluster" ? (
                  <div
                    style={{
                      position: "absolute",
                      top: 8,
                      right: 8,
                      zIndex: 3,
                      fontFamily: T.fontSans,
                      fontSize: 11,
                      fontWeight: 600,
                      color: T.black,
                      background: T.white,
                      border: `1px solid ${T.border}`,
                      borderRadius: 999,
                      padding: "4px 10px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                      pointerEvents: "none",
                    }}
                  >
                    {nodeCount} node{nodeCount === 1 ? "" : "s"}
                  </div>
                ) : null}
                <div
                  style={{
                    padding: "8px 12px",
                    fontSize: 12,
                    fontWeight: 600,
                    color: T.gray500,
                    fontFamily: T.fontSans,
                    borderBottom: `1px dashed ${T.gray300}`,
                    background: "rgba(255,255,255,0.35)",
                    flexShrink: 0,
                  }}
                >
                  {title}
                </div>
                <div style={{ flex: 1, minHeight: 0 }} />
                {connectorHandle}
              </div>
            );
          }

          if (type === "IMAGE") {
            const url = imageUrlFromJson(el);
            return (
              <div
                key={el.id}
                ref={getMeasureRef(el.id)}
                onMouseEnter={() => setHoveredElementId(el.id)}
                onMouseLeave={() =>
                  setHoveredElementId((cur) => (cur === el.id ? null : cur))
                }
                style={outerStyle}
                onMouseDown={onCardMouseDown}
              >
                {trashBtn}
                {url ? (
                  <img
                    src={url}
                    alt={el.title ?? ""}
                    style={{
                      width: "100%",
                      height: minH != null ? "calc(100% - 8px)" : "auto",
                      maxHeight: minH != null ? "100%" : 320,
                      objectFit: "contain",
                      flex: 1,
                    }}
                  />
                ) : (
                  <div
                    style={{
                      fontFamily: T.fontSans,
                      fontSize: 13,
                      color: T.gray500,
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    {el.title?.trim() || "Image"}
                  </div>
                )}
                {connectorHandle}
              </div>
            );
          }

          const markdownBlock = (
            <div className="canvas-md" style={{ color: T.black }}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeSanitize]}
              >
                {body}
              </ReactMarkdown>
            </div>
          );

          return (
            <div
              key={el.id}
              ref={getMeasureRef(el.id)}
              onMouseEnter={() => setHoveredElementId(el.id)}
              onMouseLeave={() =>
                setHoveredElementId((cur) => (cur === el.id ? null : cur))
              }
              style={outerStyle}
              onMouseDown={onCardMouseDown}
            >
              {trashBtn}
              {isAi ? (
                <div
                  style={{
                    display: "flex",
                    flex: 1,
                    minHeight: 0,
                    gap: 0,
                  }}
                >
                  <div
                    style={{
                      width: 4,
                      flexShrink: 0,
                      background: T.black,
                      borderRadius: 2,
                      marginRight: 12,
                      alignSelf: "stretch",
                    }}
                  />
                  <div
                    style={{
                      flex: 1,
                      minWidth: 0,
                      display: "flex",
                      flexDirection: "column",
                    }}
                  >
                    {markdownBlock}
                    {showProvenance ? (
                      <ProvenanceFooter kind={el.provenanceKind} />
                    ) : null}
                  </div>
                </div>
              ) : (
                <>
                  {badge}
                  <div style={innerBodyStyle}>
                    {isData ? dataDisplayValue(el) : markdownBlock}
                  </div>
                  {showProvenance ? (
                    <ProvenanceFooter kind={el.provenanceKind} />
                  ) : null}
                </>
              )}
              {connectorHandle}
            </div>
          );
        })}
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
            disabled={disabled || (key === "text" && (!canvasId || isCreatingElement))}
            title={
              title ??
              (key === "text" ? "Add text block at viewport center" : undefined)
            }
            style={{
              border: "none",
              background: active ? "rgba(255,255,255,0.15)" : "transparent",
              color: T.white,
              padding: "7px 10px",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              cursor:
                disabled || (key === "text" && (!canvasId || isCreatingElement))
                  ? "not-allowed"
                  : "pointer",
              opacity:
                disabled || (key === "text" && (!canvasId || isCreatingElement))
                  ? 0.45
                  : 1,
            }}
            onClick={() => {
              if (key === "text") {
                const spec = CREATION_BY_KIND.get("TEXT");
                if (spec) void onCreateElement(spec);
                return;
              }
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
                  const dialog = deleteDialog;
                  if (dialog.kind === "block") {
                    const id = dialog.elementId;
                    flushSync(() => {
                      setPendingRemovedElementIds((p) => ({ ...p, [id]: true }));
                      setSelectedElementId((cur) => (cur === id ? null : cur));
                      setDraggingId(null);
                      dragStartRef.current = null;
                      setDragPositions((p) => {
                        if (!(id in p)) return p;
                        const { [id]: _, ...rest } = p;
                        return rest;
                      });
                      setMeasuredHeights((p) => {
                        if (!(id in p)) return p;
                        const { [id]: _, ...rest } = p;
                        return rest;
                      });
                      setDeleteDialog(null);
                    });
                    void deleteCanvasElement(id)
                      .then(async () => {
                        await mutate();
                      })
                      .catch(() => {
                        setPendingRemovedElementIds((p) => {
                          if (!p[id]) return p;
                          const { [id]: _, ...rest } = p;
                          return rest;
                        });
                      });
                  } else {
                    const cid = dialog.connectionId;
                    flushSync(() => {
                      setPendingRemovedConnectionIds((p) => ({
                        ...p,
                        [cid]: true,
                      }));
                      setSelectedConnectionId((cur) =>
                        cur === cid ? null : cur,
                      );
                      setDeleteDialog(null);
                    });
                    void deleteCanvasConnection(cid)
                      .then(async () => {
                        await mutateConnections();
                      })
                      .catch(() => {
                        setPendingRemovedConnectionIds((p) => {
                          if (!p[cid]) return p;
                          const { [cid]: _, ...rest } = p;
                          return rest;
                        });
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
});

