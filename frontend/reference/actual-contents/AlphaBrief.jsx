import { useState, useRef, useEffect, useCallback } from "react";

// ── Design tokens ────────────────────────────────────────────────────────────
const T = {
  bg: "#f0ede8",
  bgPanel: "#f0ede8",
  sidebar: "#ebe8e3",
  white: "#ffffff",
  black: "#1a1a1a",
  blackSoft: "#111111",
  gray100: "#f7f5f2",
  gray200: "#e8e5e0",
  gray300: "#d4d0ca",
  gray400: "#b0ab9f",
  gray500: "#7a7570",
  gray600: "#5a5550",
  border: "#dddad4",
  accent: "#1a1a1a",
  userBubble: "#1a1a1a",
  aiBubble: "#ffffff",
  fontSans: "'DM Sans', system-ui, sans-serif",
  fontDisplay: "'DM Serif Display', Georgia, serif",
};

// ── SVG Logo (from image 5) ───────────────────────────────────────────────────
function AlphaBriefLogo({ size = 28, showText = true }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="100" rx="18" fill="#1a1a1a" />
        <path d="M50 15 L78 78 L50 62 L22 78 Z" fill="white" />
        <path d="M50 62 L22 78 Q35 68 50 72 Q65 68 78 78 Z" fill="rgba(255,255,255,0.35)" />
      </svg>
      {showText && (
        <span style={{ fontFamily: T.fontSans, fontWeight: 600, fontSize: size * 0.64, color: T.black, letterSpacing: "-0.02em" }}>
          AlphaBrief
        </span>
      )}
    </div>
  );
}

// ── Icons ─────────────────────────────────────────────────────────────────────
const Icon = {
  Home: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9,22 9,12 15,12 15,22" />
    </svg>
  ),
  ResearchSpace: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  ),
  Discover: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  Chat: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  Plus: ({ size = 16 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  Search: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  Send: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22,2 15,22 11,13 2,9" />
    </svg>
  ),
  Pin: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
    </svg>
  ),
  Share: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" /><polyline points="16,6 12,2 8,6" /><line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  ),
  Agent: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13,2 3,14 12,14 11,22 21,10 12,10" />
    </svg>
  ),
  Settings: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  Attach: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  ),
  Globe: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  ),
  Database: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  ),
  ChevronDown: () => (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="6,9 12,15 18,9" />
    </svg>
  ),
  ArrowUpRight: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <line x1="7" y1="17" x2="17" y2="7" /><polyline points="7,7 17,7 17,17" />
    </svg>
  ),
  Canvas: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M9 21V9" />
    </svg>
  ),
  Sources: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14,2 14,8 20,8" />
    </svg>
  ),
  Memory: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2z" /><path d="M12 8v4l3 3" />
    </svg>
  ),
  Back: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12,19 5,12 12,5" />
    </svg>
  ),
  Sidebar: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <rect x="3" y="3" width="18" height="18" rx="2" /><line x1="9" y1="3" x2="9" y2="21" />
    </svg>
  ),
  Brief: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><line x1="8" y1="13" x2="16" y2="13" /><line x1="8" y1="17" x2="13" y2="17" />
    </svg>
  ),
  PinBoard: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
    </svg>
  ),
  Cursor: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M4 4l6 18 3-7 7-3z" />
    </svg>
  ),
  Move: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <polyline points="5,9 2,12 5,15" /><polyline points="9,5 12,2 15,5" /><polyline points="15,19 12,22 9,19" /><polyline points="19,9 22,12 19,15" /><line x1="2" y1="12" x2="22" y2="12" /><line x1="12" y1="2" x2="12" y2="22" />
    </svg>
  ),
  Text: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <polyline points="4,7 4,4 20,4 20,7" /><line x1="9" y1="20" x2="15" y2="20" /><line x1="12" y1="4" x2="12" y2="20" />
    </svg>
  ),
  Pen: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  ),
  Arrow: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12,5 19,12 12,19" />
    </svg>
  ),
  Image: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21,15 16,10 5,21" />
    </svg>
  ),
  Note: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14,2 14,8 20,8" />
    </svg>
  ),
  Comment: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  ZoomMinus: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /><line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  ),
  ZoomPlus: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /><line x1="11" y1="8" x2="11" y2="14" /><line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  ),
  Expand: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <polyline points="15,3 21,3 21,9" /><polyline points="9,21 3,21 3,15" /><line x1="21" y1="3" x2="14" y2="10" /><line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  ),
};

// ── Data ──────────────────────────────────────────────────────────────────────
const QUICK_CHATS = [
  { id: 1, title: "Summarize NVDA Q1 print", time: "3m" },
  { id: 2, title: "Compare Trainium vs H200 econ...", time: "22m" },
  { id: 3, title: "GLP-1 — snack volume read", time: "1h" },
  { id: 4, title: "Uranium spot vs term — quick ma...", time: "2h" },
  { id: 5, title: "TSMC Apr revenue comme...", time: "yesterday" },
  { id: 6, title: "PJM auction — winners an...", time: "yesterday" },
  { id: 7, title: "Defense FY27 topline scenarios", time: "2d" },
];

const RESEARCH_SPACES = [
  { id: 1, title: "AI Infra · 2026", desc: "Compute, memory, packaging, and the post-Blackwell roadmap.", threads: 4, updated: "8m ago" },
  { id: 2, title: "GLP-1 second-order", desc: "Demand destruction across snack, QSR, apparel, devices.", threads: 3, updated: "3h ago" },
  { id: 3, title: "Energy transition", desc: "Uranium, grid, and the AI power thesis.", threads: 2, updated: "yesterday" },
  { id: 4, title: "Defense primes — FY27", desc: "Budget read-through and program risk.", threads: 1, updated: "yesterday" },
];

const CONVO = [
  {
    role: "user",
    text: "Summarize the bull case for Nvidia post-Blackwell in three bullets, then list the two strongest disconfirming data points.",
  },
  {
    role: "ai",
    text: "Bull case — (1) Blackwell ramp tracking ahead of plan with constraint shifting from HBM3e to advanced packaging; (2) NVLink + Spectrum-X locking in system-level lock-in beyond raw silicon; (3) Sovereign AI pipeline adds ~$8–12B of demand visibility into FY27.\n\nDisconfirming — Trainium 3 inference economics at AWS re:Invent; Google TPU v6 external availability via GCP.",
    sources: ["sec.gov", "morganstanley.com", "nvidia.com"],
  },
  {
    role: "user",
    text: "What's the read-through to AVGO and the networking names?",
  },
  {
    role: "ai",
    text: "Reading 6 sources...",
    loading: true,
  },
];

const CANVAS_CARDS = [
  { id: 1, x: 620, y: 120, type: "CLAIM", title: "CoWoS-L capacity rising — bottleneck shifting from on-wafer.", meta: "CHAT · 12:14" },
  { id: 2, x: 620, y: 260, type: "CLAIM", title: "Hyperscaler order book extends to 2027.", meta: "CHAT · 12:14" },
  { id: 3, x: 620, y: 390, type: "QUOTE", title: '"We are sold out on advanced packaging through end of 2026 and adding capacity as toolchain permits."', source: "— TSMC · Q1 2026 earnings", meta: "TRANSCRIPT · 41 PP" },
  { id: 4, x: 620, y: 570, type: "DATA", title: "+3.2% QoQ HBM", meta: "TRENDFORCE · APR" },
];

const SPACE_RESOURCES = [
  "Nvidia 10-Q · Q1 FY26",
  "Blackwell ramp — supply chain note",
  "TSMC Apr monthly revenue",
  "Jensen Huang — GTC keynote",
  "HBM3e capacity tracker",
];

const SPACE_CHATS = [
  { title: "Nvidia moat after Blackwell", time: "8m" },
  { title: "TSMC 2nm yield — A19 timing", time: "1h" },
];

// ── Sidebar ───────────────────────────────────────────────────────────────────
function Sidebar({ view, setView, activeChatId, setActiveChatId, onNewChat, isResearchSpace = false, spaceData = null, onBack }) {
  const today = new Date();
  const dayNum = String(today.getDate()).padStart(2, "0");
  const dayName = today.toLocaleDateString("en-US", { weekday: "long" });
  const month = today.toLocaleDateString("en-US", { month: "short" }).toUpperCase();
  const year = today.getFullYear();
  const week = Math.ceil(today.getDate() / 7) + (Math.floor((today.getDay() - today.getDate() % 7 + 7) / 7));

  if (isResearchSpace && spaceData) {
    return (
      <aside style={{ width: 280, minWidth: 280, background: T.sidebar, borderRight: `1px solid ${T.border}`, display: "flex", flexDirection: "column", height: "100vh" }}>
        {/* Top */}
        <div style={{ padding: "14px 16px", display: "flex", alignItems: "center", gap: 10, borderBottom: `1px solid ${T.border}` }}>
          <button onClick={onBack} style={{ background: "none", border: "none", cursor: "pointer", color: T.gray500, padding: 4, display: "flex", borderRadius: 6 }}>
            <Icon.Back />
          </button>
          <AlphaBriefLogo size={22} />
          <div style={{ marginLeft: "auto" }}>
            <button style={{ background: "none", border: "none", cursor: "pointer", color: T.gray500, padding: 4 }}>
              <Icon.Sidebar />
            </button>
          </div>
        </div>
        {/* Space info */}
        <div style={{ padding: "20px 20px 16px" }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Research Space</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: T.black, letterSpacing: "-0.02em", lineHeight: 1.2, marginBottom: 6 }}>{spaceData.title}</div>
          <div style={{ fontSize: 12, color: T.gray500, lineHeight: 1.5 }}>{spaceData.desc}</div>
        </div>
        {/* Nav tabs */}
        {[
          { key: "canvas", label: "Canvas", icon: <Icon.Canvas /> },
          { key: "sources", label: "Sources", icon: <Icon.Sources /> },
          { key: "memory", label: "Memory", icon: <Icon.Memory /> },
        ].map(({ key, label, icon }) => (
          <button key={key} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 20px", background: key === "canvas" ? T.gray200 : "none", border: "none", cursor: "pointer", width: "100%", textAlign: "left", color: T.black, fontFamily: T.fontSans, fontSize: 13, fontWeight: key === "canvas" ? 600 : 400, borderRadius: 0 }}>
            <span style={{ color: key === "canvas" ? T.black : T.gray400 }}>{icon}</span>
            {label}
          </button>
        ))}
        <div style={{ height: 1, background: T.border, margin: "12px 0" }} />
        {/* Resources */}
        <div style={{ padding: "0 20px 8px", flex: 1, overflowY: "auto" }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Resources</div>
          {SPACE_RESOURCES.map((r, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0", cursor: "pointer" }}>
              <Icon.Sources />
              <span style={{ fontSize: 12, color: T.gray600, fontFamily: T.fontSans }}>{r}</span>
            </div>
          ))}
          <div style={{ height: 1, background: T.border, margin: "12px 0" }} />
          <div style={{ fontSize: 10, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Chats</div>
          {SPACE_CHATS.map((c, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0", cursor: "pointer" }}>
              <Icon.Chat />
              <span style={{ fontSize: 12, color: T.gray600, flex: 1, fontFamily: T.fontSans }}>{c.title}</span>
              <span style={{ fontSize: 11, color: T.gray400 }}>{c.time}</span>
            </div>
          ))}
        </div>
        {/* Footer */}
        <div style={{ padding: "12px 20px", borderTop: `1px solid ${T.border}`, display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: "50%", background: T.black, color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700 }}>BZ</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: T.black, fontFamily: T.fontSans }}>Bruce Zhang</div>
            <div style={{ fontSize: 11, color: T.gray400 }}>Pro</div>
          </div>
          {/* Bottom action icons */}
          <div style={{ display: "flex", gap: 12, marginTop: 4, justifyContent: "center", padding: "0 16px 0" }}>
            {[
              { icon: <Icon.Brief />, label: "Brief" },
              { icon: <Icon.PinBoard />, label: "Pin" },
              { icon: <Icon.Share />, label: "Share" },
            ].map(({ icon, label }) => (
              <button key={label} style={{ background: "none", border: "none", cursor: "pointer", color: T.gray500, display: "flex", flexDirection: "column", alignItems: "center", gap: 3, fontSize: 10, fontFamily: T.fontSans, padding: 4 }}>
                {icon}
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside style={{ width: 280, minWidth: 280, background: T.sidebar, borderRight: `1px solid ${T.border}`, display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Logo + date */}
      <div style={{ padding: "18px 20px 12px" }}>
        <AlphaBriefLogo size={26} />
        <div style={{ marginTop: 18 }}>
          <div style={{ fontSize: 12, color: T.gray400, fontFamily: T.fontSans }}>{dayName}</div>
          <div style={{ fontSize: 52, fontWeight: 800, color: T.black, lineHeight: 1, letterSpacing: "-0.03em", fontFamily: T.fontSans }}>{dayNum}</div>
          <div style={{ fontSize: 11, color: T.gray400, letterSpacing: "0.05em", marginTop: 2, fontFamily: T.fontSans }}>
            {month} · {year} · W{week}
          </div>
        </div>
      </div>
      {/* New chat */}
      <div style={{ padding: "0 12px 12px" }}>
        <button onClick={onNewChat} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", padding: "10px 16px", background: T.black, color: "white", border: "none", borderRadius: 10, cursor: "pointer", fontFamily: T.fontSans, fontSize: 13, fontWeight: 600 }}>
          <span style={{ display: "flex", alignItems: "center", gap: 8 }}><Icon.Plus size={14} /> New chat</span>
          <span style={{ fontSize: 11, opacity: 0.5, background: "rgba(255,255,255,0.15)", padding: "2px 6px", borderRadius: 4 }}>⌘N</span>
        </button>
      </div>
      {/* Search */}
      <div style={{ padding: "0 12px 12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: T.gray100, border: `1px solid ${T.border}`, borderRadius: 8 }}>
          <Icon.Search />
          <span style={{ fontSize: 13, color: T.gray400, fontFamily: T.fontSans, flex: 1 }}>Search...</span>
          <span style={{ fontSize: 11, color: T.gray400 }}>⌘K</span>
        </div>
      </div>
      {/* Nav */}
      {[
        { key: "home", label: "Home", icon: <Icon.Home /> },
        { key: "research", label: "Research space", icon: <Icon.ResearchSpace />, badge: 4 },
        { key: "discover", label: "Discover", icon: <Icon.Discover /> },
      ].map(({ key, label, icon, badge }) => (
        <button key={key} onClick={() => setView(key)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 16px", background: view === key ? T.gray200 : "none", border: "none", cursor: "pointer", width: "100%", textAlign: "left", color: T.black, fontFamily: T.fontSans, fontSize: 13, fontWeight: view === key ? 600 : 400, borderRadius: 0 }}>
          <span style={{ color: view === key ? T.black : T.gray400 }}>{icon}</span>
          <span style={{ flex: 1 }}>{label}</span>
          {badge && <span style={{ fontSize: 11, color: T.gray400 }}>{badge}</span>}
        </button>
      ))}
      <div style={{ height: 1, background: T.border, margin: "12px 0" }} />
      {/* Quick chats */}
      <div style={{ padding: "0 16px 6px" }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>Quick Chats</div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "0 8px" }}>
        {QUICK_CHATS.map((c) => (
          <button key={c.id} onClick={() => setActiveChatId(c.id)} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 10px", width: "100%", background: activeChatId === c.id ? T.gray200 : "none", border: "none", cursor: "pointer", borderRadius: 8, textAlign: "left" }}>
            <span style={{ color: T.gray400 }}><Icon.Chat /></span>
            <span style={{ flex: 1, fontSize: 12, color: T.gray700, fontFamily: T.fontSans, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.title}</span>
            <span style={{ fontSize: 11, color: T.gray400, whiteSpace: "nowrap" }}>{c.time}</span>
          </button>
        ))}
      </div>
      {/* User */}
      <div style={{ padding: "12px 16px", borderTop: `1px solid ${T.border}`, display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 30, height: 30, borderRadius: "50%", background: T.black, color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700 }}>BZ</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: T.black, fontFamily: T.fontSans }}>Bruce Zhang</div>
          <div style={{ fontSize: 11, color: T.gray400 }}>Pro</div>
        </div>
        <button style={{ background: "none", border: "none", cursor: "pointer", color: T.gray400 }}><Icon.Settings /></button>
      </div>
    </aside>
  );
}

// ── Chat Input Bar ─────────────────────────────────────────────────────────────
function ChatInputBar({ onSend, placeholder = "Ask, or paste a URL to research..." }) {
  const [val, setVal] = useState("");
  const [mode, setMode] = useState("Standard research");

  const handleSend = () => {
    if (val.trim()) { onSend(val); setVal(""); }
  };

  return (
    <div style={{ padding: "16px 24px 20px", background: T.bgPanel }}>
      <div style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 14, boxShadow: "0 2px 12px rgba(0,0,0,0.06)", overflow: "hidden" }}>
        <textarea
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          placeholder={placeholder}
          rows={1}
          style={{ width: "100%", padding: "14px 16px 8px", border: "none", outline: "none", resize: "none", fontFamily: T.fontSans, fontSize: 14, color: T.black, background: "transparent", boxSizing: "border-box" }}
        />
        <div style={{ display: "flex", alignItems: "center", padding: "8px 12px 10px", gap: 8 }}>
          {[<Icon.Attach />, <Icon.Globe />, <Icon.Database />].map((icon, i) => (
            <button key={i} style={{ background: "none", border: "none", cursor: "pointer", color: T.gray400, padding: 6, borderRadius: 6, display: "flex" }}>{icon}</button>
          ))}
          <div style={{ flex: 1 }} />
          <button onClick={() => setMode(mode === "Standard research" ? "Quick research" : mode === "Quick research" ? "Deep research" : "Standard research")}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 12px", border: `1px solid ${T.border}`, borderRadius: 8, background: T.white, cursor: "pointer", fontFamily: T.fontSans, fontSize: 12, fontWeight: 500, color: T.black }}>
            {mode} <Icon.ChevronDown />
          </button>
          <button onClick={handleSend} style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", background: T.black, color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontFamily: T.fontSans, fontSize: 12, fontWeight: 600 }}>
            <Icon.Send /> Send
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Home View: initial empty state ────────────────────────────────────────────
function HomeEmptyState({ onSend }) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Top bar */}
      <div style={{ height: 52, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", borderBottom: `1px solid ${T.border}`, background: T.bgPanel }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: T.gray500, fontFamily: T.fontSans }}>
          <Icon.Agent />
          <span style={{ fontWeight: 600, color: T.black }}>Agent</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {[{ icon: <Icon.Pin />, label: "Pin" }, { icon: <Icon.Share />, label: "Share" }].map(({ icon, label }) => (
            <button key={label} style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 12px", border: `1px solid ${T.border}`, borderRadius: 8, background: T.white, cursor: "pointer", fontFamily: T.fontSans, fontSize: 12, color: T.gray600 }}>
              {icon} {label}
            </button>
          ))}
        </div>
      </div>
      {/* Center empty state */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 40 }}>
        <AlphaBriefLogo size={40} showText={false} />
        <div style={{ marginTop: 24, fontSize: 22, fontWeight: 700, color: T.black, fontFamily: T.fontSans, letterSpacing: "-0.02em", textAlign: "center" }}>
          Ready when you are, Bruce.
        </div>
        <div style={{ marginTop: 8, fontSize: 14, color: T.gray400, fontFamily: T.fontSans, textAlign: "center" }}>
          Ask anything, paste a URL, or drop in a document to get started.
        </div>
      </div>
      <ChatInputBar onSend={onSend} />
    </div>
  );
}

// ── Home View: active chat ────────────────────────────────────────────────────
function HomeChatView({ messages, onSend }) {
  const bottomRef = useRef(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Top bar */}
      <div style={{ height: 52, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", borderBottom: `1px solid ${T.border}`, background: T.bgPanel }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontFamily: T.fontSans }}>
          <Icon.Agent />
          <span style={{ fontWeight: 600, color: T.black }}>Agent</span>
          <span style={{ color: T.gray300, margin: "0 4px" }}>·</span>
          <span style={{ color: T.gray400 }}>brief-4</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {[{ icon: <Icon.Pin />, label: "Pin" }, { icon: <Icon.Share />, label: "Share" }].map(({ icon, label }) => (
            <button key={label} style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 12px", border: `1px solid ${T.border}`, borderRadius: 8, background: T.white, cursor: "pointer", fontFamily: T.fontSans, fontSize: 12, color: T.gray600 }}>
              {icon} {label}
            </button>
          ))}
        </div>
      </div>
      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "32px 60px" }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 24, display: "flex", flexDirection: "column", alignItems: m.role === "user" ? "flex-end" : "flex-start" }}>
            {m.role === "user" ? (
              <div style={{ maxWidth: "60%", background: T.userBubble, color: "white", padding: "12px 18px", borderRadius: 14, fontFamily: T.fontSans, fontSize: 14, lineHeight: 1.6 }}>
                {m.text}
              </div>
            ) : (
              <div style={{ maxWidth: "80%" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                  <div style={{ width: 22, height: 22, background: T.black, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <svg width="12" height="12" viewBox="0 0 100 100"><polygon points="13,2 3,14 12,14 11,22 21,10 12,10" fill="white" /><path d="M50 15 L78 78 L50 62 L22 78 Z" fill="white" /></svg>
                  </div>
                  <span style={{ fontFamily: T.fontSans, fontSize: 11, fontWeight: 700, color: T.black, letterSpacing: "0.05em", textTransform: "uppercase" }}>AlphaBrief</span>
                </div>
                <div style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 12, padding: "16px 20px", fontFamily: T.fontSans, fontSize: 14, color: T.black, lineHeight: 1.7 }}>
                  {m.loading ? (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, color: T.gray400 }}>
                      <div style={{ width: 6, height: 6, borderRadius: "50%", background: T.gray300, animation: "pulse 1.2s ease infinite" }} />
                      {m.text}
                    </div>
                  ) : (
                    <>
                      {m.text.split("\n\n").map((p, j) => <p key={j} style={{ margin: j > 0 ? "12px 0 0" : 0 }}>{p}</p>)}
                      {m.sources && (
                        <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
                          {m.sources.map((s, j) => (
                            <div key={j} style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 11, color: T.gray500, fontFamily: T.fontSans }}>
                              <Icon.Database /> [{j + 1}] {s}
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <ChatInputBar onSend={onSend} />
    </div>
  );
}

// ── Research Spaces View ───────────────────────────────────────────────────────
function ResearchView({ spaces, onSelectSpace, onAddSpace }) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh" }}>
      <div style={{ height: 52, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px", borderBottom: `1px solid ${T.border}`, background: T.bgPanel }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: T.fontSans, fontSize: 13, color: T.gray500 }}>
          <Icon.ResearchSpace />
          <span style={{ fontWeight: 600, color: T.black }}>Research spaces</span>
          {spaces.length > 0 && <><span style={{ color: T.gray300 }}>·</span><span>{spaces.length} active</span></>}
        </div>
        <button onClick={onAddSpace} style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", background: T.black, color: "white", border: "none", borderRadius: 10, cursor: "pointer", fontFamily: T.fontSans, fontSize: 12, fontWeight: 600 }}>
          <Icon.Plus size={12} /> New space
        </button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "48px 60px" }}>
        <div style={{ marginBottom: 4, fontSize: 11, fontWeight: 700, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.08em" }}>Spaces</div>
        <h1 style={{ fontFamily: T.fontSans, fontSize: 48, fontWeight: 800, color: T.black, letterSpacing: "-0.03em", margin: "8px 0 12px", lineHeight: 1.1 }}>Pick a research space to enter</h1>
        <p style={{ fontFamily: T.fontSans, fontSize: 14, color: T.gray500, marginBottom: 40 }}>Each space holds its own threads, sources, memory, and canvas. Open one to dive into the editor.</p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {spaces.map((sp) => (
            <button key={sp.id} onClick={() => onSelectSpace(sp)} style={{ textAlign: "left", background: T.white, border: `1px solid ${T.border}`, borderRadius: 14, padding: "24px 26px", cursor: "pointer", transition: "box-shadow 0.15s, border-color 0.15s", position: "relative" }}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.08)"; e.currentTarget.style.borderColor = T.gray300; }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = "none"; e.currentTarget.style.borderColor = T.border; }}>
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <Icon.ResearchSpace />
                  <span style={{ fontFamily: T.fontSans, fontSize: 16, fontWeight: 700, color: T.black, letterSpacing: "-0.01em" }}>{sp.title}</span>
                </div>
                <Icon.ArrowUpRight />
              </div>
              <p style={{ fontFamily: T.fontSans, fontSize: 13, color: T.gray500, margin: "10px 0 16px", lineHeight: 1.5 }}>{sp.desc}</p>
              <div style={{ display: "flex", gap: 8, fontSize: 11, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                <span>{sp.threads} threads</span>
                <span>·</span>
                <span>Updated {sp.updated}</span>
              </div>
            </button>
          ))}

          {/* Add new space card */}
          <button onClick={onAddSpace} style={{ textAlign: "center", background: "transparent", border: `1.5px dashed ${T.gray300}`, borderRadius: 14, padding: "40px 26px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", minHeight: 150, transition: "border-color 0.15s, background 0.15s" }}
            onMouseEnter={(e) => { e.currentTarget.style.background = T.gray100; e.currentTarget.style.borderColor = T.gray400; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = T.gray300; }}>
            <div style={{ width: 52, height: 52, borderRadius: "50%", background: "rgba(180,175,168,0.18)", backdropFilter: "blur(6px)", display: "flex", alignItems: "center", justifyContent: "center", color: T.gray400 }}>
              <Icon.Plus size={22} />
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Space Loading Screen ───────────────────────────────────────────────────────
function SpaceLoading({ spaceTitle }) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: T.bg, gap: 0 }}>
      <div style={{ width: 52, height: 52, borderRadius: "50%", background: T.gray200, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 20 }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={T.gray500} strokeWidth="1.8" strokeLinecap="round">
          <path d="M21 12a9 9 0 1 1-6.219-8.56" style={{ strokeDasharray: 40, animation: "spin 1.1s linear infinite" }} />
        </svg>
      </div>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", color: T.gray400, textTransform: "uppercase", marginBottom: 10, fontFamily: T.fontSans }}>Opening Space</div>
      <h2 style={{ fontFamily: T.fontSans, fontSize: 36, fontWeight: 800, color: T.black, letterSpacing: "-0.03em", margin: 0, lineHeight: 1.1 }}>{spaceTitle}</h2>
      <p style={{ marginTop: 12, fontSize: 13, color: T.gray400, fontFamily: T.fontSans }}>Loading threads, sources, memory, and canvas state...</p>
      <style>{`@keyframes spin { from { stroke-dashoffset: 40; } to { stroke-dashoffset: -40; } }`}</style>
    </div>
  );
}

// ── Infinite Canvas ────────────────────────────────────────────────────────────
function InfiniteCanvas({ cards }) {
  const canvasRef = useRef(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(0.92);
  const [isPanning, setIsPanning] = useState(false);
  const startPan = useRef(null);

  const onMouseDown = (e) => {
    if (e.button === 1 || e.altKey) {
      setIsPanning(true);
      startPan.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
    }
  };
  const onMouseMove = useCallback((e) => {
    if (!isPanning || !startPan.current) return;
    setPan({ x: e.clientX - startPan.current.x, y: e.clientY - startPan.current.y });
  }, [isPanning]);
  const onMouseUp = () => { setIsPanning(false); startPan.current = null; };

  const onWheel = (e) => {
    e.preventDefault();
    if (e.ctrlKey || e.metaKey) {
      setZoom((z) => Math.min(2, Math.max(0.3, z - e.deltaY * 0.002)));
    } else {
      setPan((p) => ({ x: p.x - e.deltaX, y: p.y - e.deltaY }));
    }
  };

  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const cardStyle = (type) => {
    const base = { position: "absolute", background: T.white, border: `1px solid ${T.border}`, borderRadius: 10, padding: "14px 16px", width: 220, boxShadow: "0 2px 8px rgba(0,0,0,0.06)", cursor: "default" };
    return base;
  };

  return (
    <div ref={canvasRef} onMouseDown={onMouseDown} onMouseMove={onMouseMove} onMouseUp={onMouseUp} onMouseLeave={onMouseUp}
      style={{ flex: 1, overflow: "hidden", position: "relative", cursor: isPanning ? "grabbing" : "default", background: T.bg, backgroundImage: `radial-gradient(circle, ${T.gray300} 1px, transparent 1px)`, backgroundSize: `${24 * zoom}px ${24 * zoom}px`, backgroundPosition: `${pan.x}px ${pan.y}px` }}>
      {/* Zoom controls */}
      <div style={{ position: "absolute", top: 16, right: 16, zIndex: 10, display: "flex", gap: 4, background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, padding: 4 }}>
        <button onClick={() => setZoom(z => Math.max(0.3, z - 0.1))} style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 8px", color: T.gray500, display: "flex" }}><Icon.ZoomMinus /></button>
        <span style={{ fontFamily: T.fontSans, fontSize: 12, color: T.gray500, display: "flex", alignItems: "center", padding: "0 4px" }}>{Math.round(zoom * 100)}%</span>
        <button onClick={() => setZoom(z => Math.min(2, z + 0.1))} style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 8px", color: T.gray500, display: "flex" }}><Icon.ZoomPlus /></button>
        <div style={{ width: 1, background: T.border, margin: "4px 0" }} />
        <button onClick={() => { setPan({ x: 0, y: 0 }); setZoom(0.92); }} style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 8px", color: T.gray500, display: "flex" }}><Icon.Expand /></button>
      </div>

      {/* Canvas content */}
      <div style={{ position: "absolute", top: 0, left: 0, transformOrigin: "0 0", transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}>
        {/* Main canvas title */}
        <div style={{ position: "absolute", left: 60, top: 60, width: 480 }}>
          <h2 style={{ fontFamily: T.fontSans, fontSize: 32, fontWeight: 800, color: T.black, letterSpacing: "-0.02em", margin: "0 0 20px" }}>Nvidia moat — working canvas</h2>
          <p style={{ fontFamily: T.fontSans, fontSize: 14, color: T.gray400, lineHeight: 1.7, margin: 0 }}>
            Drop quotes, charts, and screenshots here. Drag anything. Click any text to edit. Imported blocks from the chat are pinned on the right and stay linked to their source.
          </p>
        </div>

        {/* Cards */}
        {cards.map((card) => (
          <div key={card.id} style={{ ...cardStyle(card.type), left: card.x, top: card.y }}>
            <div style={{ fontSize: 9, fontWeight: 800, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>{card.type} <span style={{ fontSize: 14 }}>• • • •</span></div>
            <div style={{ fontFamily: T.fontSans, fontSize: 13, color: card.type === "QUOTE" ? T.gray600 : T.black, lineHeight: 1.5, marginBottom: 8, fontStyle: card.type === "QUOTE" ? "italic" : "normal" }}>
              {card.type === "DATA" ? <span style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>{card.title}</span> : card.title}
            </div>
            {card.source && <div style={{ fontSize: 11, color: T.gray400, marginBottom: 6, fontFamily: T.fontSans }}>{card.source}</div>}
            <div style={{ fontSize: 10, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: "0.06em" }}>{card.meta}</div>
          </div>
        ))}
      </div>

      {/* Bottom toolbar */}
      <div style={{ position: "absolute", bottom: 20, left: "50%", transform: "translateX(-50%)", background: T.black, borderRadius: 12, padding: "10px 16px", display: "flex", gap: 4, boxShadow: "0 4px 24px rgba(0,0,0,0.2)" }}>
        {[<Icon.Cursor />, <Icon.Move />, <Icon.Text />, <Icon.Pen />, <Icon.Arrow />, <Icon.Image />, <Icon.Note />, <Icon.Comment />].map((icon, i) => (
          <button key={i} style={{ background: i === 0 ? "rgba(255,255,255,0.15)" : "none", border: "none", cursor: "pointer", color: "white", padding: "7px 10px", borderRadius: 8, display: "flex" }}>{icon}</button>
        ))}
      </div>
    </div>
  );
}

// ── Research Space Workspace ───────────────────────────────────────────────────
function ResearchWorkspace({ spaceData, onBack }) {
  const [chatMessages, setChatMessages] = useState(CONVO);

  const handleSend = (text) => {
    setChatMessages((m) => [...m, { role: "user", text }, { role: "ai", text: "Analyzing sources...", loading: true }]);
  };

  return (
    <div style={{ flex: 1, display: "flex", height: "100vh", overflow: "hidden" }}>
      <Sidebar isResearchSpace spaceData={spaceData} onBack={onBack} />

      {/* AI Intelligence toggle bar */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ height: 52, display: "flex", alignItems: "center", padding: "0 16px", borderBottom: `1px solid ${T.border}`, background: T.bgPanel }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: T.black, borderRadius: 20, padding: "6px 14px" }}>
            <Icon.Agent />
            <span style={{ fontFamily: T.fontSans, fontSize: 12, fontWeight: 600, color: "white" }}>AI Intelligence</span>
            <div style={{ width: 32, height: 18, background: "#4ade80", borderRadius: 10, position: "relative", marginLeft: 4 }}>
              <div style={{ position: "absolute", right: 2, top: 2, width: 14, height: 14, borderRadius: "50%", background: "white" }} />
            </div>
          </div>
        </div>

        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {/* Infinite Canvas */}
          <InfiniteCanvas cards={CANVAS_CARDS} />

          {/* Right chat panel */}
          <div style={{ width: 380, minWidth: 380, borderLeft: `1px solid ${T.border}`, display: "flex", flexDirection: "column", background: T.bgPanel }}>
            {/* Chat header */}
            <div style={{ padding: "14px 16px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: T.fontSans, fontSize: 13, fontWeight: 600, color: T.black }}>
                <Icon.Agent /> Nvidia moat after Blackwell
              </div>
              <button style={{ fontFamily: T.fontSans, fontSize: 12, color: T.gray400, background: "none", border: "none", cursor: "pointer" }}>Clear</button>
            </div>
            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
              {chatMessages.map((m, i) => (
                <div key={i} style={{ marginBottom: 16 }}>
                  {m.role === "user" ? (
                    <div style={{ background: T.userBubble, color: "white", padding: "10px 14px", borderRadius: 12, fontFamily: T.fontSans, fontSize: 13, lineHeight: 1.6, marginLeft: 20 }}>
                      {m.text}
                    </div>
                  ) : (
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                        <div style={{ width: 18, height: 18, background: T.black, borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <svg width="10" height="10" viewBox="0 0 100 100"><path d="M50 15 L78 78 L50 62 L22 78 Z" fill="white" /></svg>
                        </div>
                        <span style={{ fontFamily: T.fontSans, fontSize: 10, fontWeight: 700, color: T.black, textTransform: "uppercase", letterSpacing: "0.06em" }}>AlphaBrief</span>
                      </div>
                      <div style={{ background: T.white, border: `1px solid ${T.border}`, borderRadius: 10, padding: "12px 14px", fontFamily: T.fontSans, fontSize: 12.5, color: T.black, lineHeight: 1.7 }}>
                        {m.loading ? (
                          <div style={{ display: "flex", alignItems: "center", gap: 6, color: T.gray400 }}>
                            <div style={{ width: 5, height: 5, borderRadius: "50%", background: T.gray300 }} /> {m.text}
                          </div>
                        ) : (
                          <>
                            {m.text.split("\n\n").map((p, j) => <p key={j} style={{ margin: j > 0 ? "8px 0 0" : 0 }}>{p}</p>)}
                            {m.sources && (
                              <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
                                {m.sources.map((s, j) => (
                                  <div key={j} style={{ display: "flex", alignItems: "center", gap: 4, padding: "3px 8px", border: `1px solid ${T.border}`, borderRadius: 5, fontSize: 10, color: T.gray500 }}>
                                    <Icon.Database /> [{j + 1}] {s}
                                  </div>
                                ))}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <ChatInputBar onSend={handleSend} placeholder="Ask, or paste a URL to research..." />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── App Shell ─────────────────────────────────────────────────────────────────
export default function App() {
  const [view, setView] = useState("home"); // home | research | workspace
  const [chatStarted, setChatStarted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [spaces, setSpaces] = useState(RESEARCH_SPACES);
  const [selectedSpace, setSelectedSpace] = useState(null);
  const [loadingSpace, setLoadingSpace] = useState(false);

  const handleNewChat = () => {
    setChatStarted(false);
    setMessages([]);
    setActiveChatId(null);
    setView("home");
  };

  const handleSendHome = (text) => {
    setChatStarted(true);
    setMessages([
      { role: "user", text },
      { role: "ai", text: "Analyzing sources...", loading: true },
    ]);
    setTimeout(() => {
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = { role: "ai", text: "Here's what I found based on current market data and your research context.", sources: ["sec.gov", "bloomberg.com"] };
        return next;
      });
    }, 2000);
  };

  const handleSelectSpace = (sp) => {
    setSelectedSpace(sp);
    setLoadingSpace(true);
    setTimeout(() => { setLoadingSpace(false); setView("workspace"); }, 1800);
  };

  const handleAddSpace = () => {
    const title = `New Space · ${spaces.length + 1}`;
    setSpaces((s) => [...s, { id: Date.now(), title, desc: "Add a description for this research space.", threads: 0, updated: "just now" }]);
  };

  // Workspace view — full override
  if (view === "workspace" && selectedSpace) {
    return (
      <div style={{ display: "flex", height: "100vh", background: T.bg, fontFamily: T.fontSans }}>
        <style>{`* { box-sizing: border-box; margin: 0; padding: 0; } @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
        <ResearchWorkspace spaceData={selectedSpace} onBack={() => { setView("research"); setSelectedSpace(null); }} />
      </div>
    );
  }

  // Loading screen
  if (loadingSpace && selectedSpace) {
    return (
      <div style={{ display: "flex", height: "100vh", background: T.bg, fontFamily: T.fontSans }}>
        <style>{`* { box-sizing: border-box; margin: 0; padding: 0; }`}</style>
        <SpaceLoading spaceTitle={selectedSpace.title} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", height: "100vh", background: T.bg, fontFamily: T.fontSans }}>
      <style>{`* { box-sizing: border-box; margin: 0; padding: 0; } @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} } body { font-family: 'DM Sans', system-ui, sans-serif; }`}</style>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=DM+Serif+Display&display=swap" rel="stylesheet" />

      <Sidebar view={view} setView={setView} activeChatId={activeChatId} setActiveChatId={setActiveChatId} onNewChat={handleNewChat} />

      {view === "home" && !chatStarted && <HomeEmptyState onSend={handleSendHome} />}
      {view === "home" && chatStarted && <HomeChatView messages={messages} onSend={handleSendHome} />}
      {view === "research" && <ResearchView spaces={spaces} onSelectSpace={handleSelectSpace} onAddSpace={handleAddSpace} />}
      {view === "discover" && (
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: T.gray400, fontFamily: T.fontSans }}>
          Discover coming soon
        </div>
      )}
    </div>
  );
}
