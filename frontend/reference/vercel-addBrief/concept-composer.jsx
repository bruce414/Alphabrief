/* global React */
// Concept 1 — COMPOSER (restyled to match v0 landing aesthetic)
// Modern SaaS — clean white surface, soft borders, violet primary,
// sans-only type, rounded corners, subtle gradient hero.

const composerStyles = {
  root: {
    width: "100%",
    height: "100%",
    display: "flex",
    flexDirection: "column",
    background: "#ffffff",
    fontFamily: "var(--ls-font)",
    color: "var(--ls-fg)",
    position: "relative",
    overflow: "hidden",
  },

  /* subtle hero gradient like landing */
  bgGlow: {
    position: "absolute",
    top: -200, left: "50%", transform: "translateX(-50%)",
    width: 1100, height: 700,
    background: "radial-gradient(ellipse at top, rgba(139, 92, 246, 0.10), rgba(139, 92, 246, 0.02) 45%, transparent 70%)",
    pointerEvents: "none",
    zIndex: 0,
  },

  /* TOP NAV */
  topbar: {
    position: "relative",
    zIndex: 2,
    height: 64,
    display: "grid",
    gridTemplateColumns: "1fr auto 1fr",
    alignItems: "center",
    padding: "0 28px",
    borderBottom: "1px solid var(--ls-border)",
    background: "rgba(255,255,255,0.72)",
    backdropFilter: "saturate(180%) blur(8px)",
    flexShrink: 0,
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: 9,
    fontFamily: "var(--ls-font)",
    fontSize: 16,
    fontWeight: 600,
    letterSpacing: "-0.015em",
    color: "var(--ls-fg)",
    justifySelf: "start",
  },
  brandMark: {
    width: 22, height: 22,
    borderRadius: 6,
    background: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontSize: 12,
    fontWeight: 700,
    fontFamily: "var(--ls-font)",
    letterSpacing: "-0.02em",
    boxShadow: "0 1px 2px rgba(99, 102, 241, 0.25)",
  },

  navCenter: {
    display: "inline-flex",
    alignItems: "center",
    gap: 2,
    padding: 4,
    borderRadius: 999,
    border: "1px solid var(--ls-border)",
    background: "var(--ls-muted)",
    justifySelf: "center",
  },
  navItem: (active) => ({
    fontFamily: "var(--ls-font)",
    fontSize: 13,
    fontWeight: 500,
    letterSpacing: "-0.005em",
    padding: "6px 14px",
    borderRadius: 999,
    color: active ? "var(--ls-fg)" : "var(--ls-muted-fg)",
    background: active ? "#ffffff" : "transparent",
    boxShadow: active ? "0 1px 2px rgba(15, 23, 42, 0.04), 0 0 0 1px var(--ls-border)" : "none",
    cursor: "pointer",
    transition: "color .15s, background .15s",
  }),

  topRight: {
    justifySelf: "end",
    display: "flex",
    alignItems: "center",
    gap: 12,
    fontSize: 13,
    color: "var(--ls-muted-fg)",
  },
  badgePill: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "5px 12px",
    borderRadius: 999,
    border: "1px solid var(--ls-border)",
    background: "var(--ls-muted)",
    fontSize: 12,
    color: "var(--ls-muted-fg)",
  },
  avatar: {
    width: 30, height: 30,
    borderRadius: "50%",
    background: "linear-gradient(135deg, #ede9fe, #e0e7ff)",
    border: "1px solid var(--ls-border)",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 11,
    fontWeight: 600,
    color: "#5b3fc9",
    letterSpacing: "0.02em",
  },

  /* BODY */
  body: {
    position: "relative",
    zIndex: 1,
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingTop: 84,
    paddingBottom: 40,
    overflowY: "auto",
  },
  hero: {
    width: 760,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },

  statusPill: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "5px 14px",
    borderRadius: 999,
    border: "1px solid var(--ls-border)",
    background: "rgba(248,250,252,0.6)",
    fontSize: 13,
    color: "var(--ls-muted-fg)",
    marginBottom: 22,
  },
  statusDot: {
    width: 7, height: 7,
    borderRadius: "50%",
    background: "#22c55e",
    boxShadow: "0 0 0 3px rgba(34,197,94,0.15)",
  },

  prompt: {
    fontFamily: "var(--ls-font)",
    fontSize: 40,
    fontWeight: 700,
    lineHeight: 1.1,
    letterSpacing: "-0.03em",
    color: "var(--ls-fg)",
    textAlign: "center",
    marginBottom: 12,
  },
  promptAccent: {
    background: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 60%, #4f46e5 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  subPrompt: {
    fontSize: 16,
    color: "var(--ls-muted-fg)",
    textAlign: "center",
    marginBottom: 32,
    maxWidth: 540,
    lineHeight: 1.5,
  },

  /* INPUT */
  inputShell: {
    width: "100%",
    background: "#ffffff",
    border: "1px solid var(--ls-border)",
    borderRadius: 16,
    padding: "20px 22px 14px",
    boxShadow: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px -12px rgba(99,102,241,0.18)",
  },
  input: {
    width: "100%",
    border: "none",
    outline: "none",
    background: "transparent",
    fontFamily: "var(--ls-font)",
    fontSize: 15.5,
    color: "var(--ls-fg)",
    minHeight: 28,
    lineHeight: 1.5,
  },
  inputCaret: {
    display: "inline-block",
    width: 1.5, height: 18,
    background: "#6366f1",
    verticalAlign: "middle",
    marginLeft: 1,
    animation: "ab-blink 1s step-end infinite",
  },
  inputBar: {
    marginTop: 16,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 12,
    borderTop: "1px solid var(--ls-border)",
  },
  sourceTabs: {
    display: "flex",
    gap: 4,
    flexWrap: "wrap",
  },
  sourceTab: (active) => ({
    fontFamily: "var(--ls-font)",
    fontSize: 12.5,
    fontWeight: 500,
    letterSpacing: "-0.003em",
    padding: "6px 12px",
    color: active ? "var(--ls-fg)" : "var(--ls-muted-fg)",
    background: active ? "var(--ls-muted)" : "transparent",
    border: active ? "1px solid var(--ls-border)" : "1px solid transparent",
    borderRadius: 999,
    cursor: "pointer",
    display: "flex", alignItems: "center", gap: 6,
    transition: "all .15s",
  }),
  generate: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    height: 36,
    padding: "0 16px",
    background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
    color: "#ffffff",
    border: "none",
    borderRadius: 999,
    fontFamily: "var(--ls-font)",
    fontSize: 13,
    fontWeight: 600,
    letterSpacing: "-0.005em",
    boxShadow: "0 1px 2px rgba(79, 70, 229, 0.25), 0 4px 12px -2px rgba(99, 102, 241, 0.30)",
  },
  kbdLight: {
    fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
    fontSize: 10.5,
    padding: "1px 6px",
    borderRadius: 4,
    background: "rgba(255,255,255,0.18)",
    color: "rgba(255,255,255,0.9)",
    letterSpacing: 0,
  },

  /* SUGGESTIONS */
  suggestRow: {
    width: "100%",
    marginTop: 18,
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    justifyContent: "center",
  },
  suggest: {
    fontFamily: "var(--ls-font)",
    fontSize: 12.5,
    fontWeight: 500,
    color: "var(--ls-muted-fg)",
    padding: "7px 14px",
    border: "1px solid var(--ls-border)",
    borderRadius: 999,
    background: "#ffffff",
    cursor: "pointer",
    transition: "all .15s",
  },

  /* RESUME STRIP */
  resumeStrip: {
    width: 760,
    marginTop: 56,
    display: "flex",
    alignItems: "stretch",
    gap: 14,
  },
  resumeCard: {
    flex: 1,
    border: "1px solid var(--ls-border)",
    borderRadius: 16,
    padding: "16px 18px",
    background: "#ffffff",
    display: "flex", flexDirection: "column", gap: 10,
    transition: "border-color .15s, box-shadow .15s",
  },
  resumeLabel: {
    fontFamily: "var(--ls-font)", fontSize: 11.5,
    fontWeight: 500,
    letterSpacing: "0.005em",
    color: "var(--ls-muted-fg)",
    display: "flex", alignItems: "center", gap: 7,
  },
  resumeDot: {
    width: 6, height: 6, borderRadius: "50%",
    background: "#8b5cf6",
    boxShadow: "0 0 0 3px rgba(139, 92, 246, 0.15)",
  },
  resumeTitle: {
    fontFamily: "var(--ls-font)",
    fontSize: 15,
    fontWeight: 600,
    lineHeight: 1.35,
    letterSpacing: "-0.012em",
    color: "var(--ls-fg)",
  },
  resumeBar: {
    height: 4,
    background: "var(--ls-muted)",
    borderRadius: 999,
    position: "relative",
    marginTop: "auto",
    overflow: "hidden",
  },
  resumeBarFill: (p) => ({
    position: "absolute",
    left: 0, top: 0, bottom: 0,
    width: `${p * 100}%`,
    borderRadius: 999,
    background: "linear-gradient(90deg, #8b5cf6, #6366f1)",
  }),
  resumeMeta: {
    display: "flex", justifyContent: "space-between",
    fontFamily: "var(--ls-font)",
    fontSize: 12,
    color: "var(--ls-muted-fg)",
    fontWeight: 500,
  },

  /* RECENTS */
  recentsSection: { width: 760, marginTop: 60 },
  sectionHead: {
    display: "flex", alignItems: "baseline", justifyContent: "space-between",
    paddingBottom: 12,
    borderBottom: "1px solid var(--ls-border)",
    marginBottom: 4,
  },
  sectionTitle: {
    fontFamily: "var(--ls-font)",
    fontSize: 14,
    fontWeight: 600,
    letterSpacing: "-0.01em",
    color: "var(--ls-fg)",
  },
  sectionSub: {
    fontFamily: "var(--ls-font)", fontSize: 12,
    color: "var(--ls-muted-fg)",
    fontWeight: 500,
  },
  sectionLink: {
    fontFamily: "var(--ls-font)", fontSize: 13,
    fontWeight: 500,
    color: "#6366f1",
    cursor: "pointer",
  },
  recentRow: {
    display: "grid",
    gridTemplateColumns: "70px 1fr 200px 60px 70px",
    alignItems: "center",
    padding: "14px 4px",
    borderBottom: "1px solid var(--ls-border)",
    gap: 16,
    borderRadius: 8,
  },
  recentDate: {
    fontFamily: "var(--ls-font)", fontSize: 12,
    color: "var(--ls-muted-fg)",
    fontWeight: 500,
  },
  recentTitle: {
    fontFamily: "var(--ls-font)",
    fontSize: 14.5,
    fontWeight: 500,
    lineHeight: 1.35,
    letterSpacing: "-0.01em",
    color: "var(--ls-fg)",
  },
  recentTags: { display: "flex", gap: 5, flexWrap: "nowrap", overflow: "hidden" },
  recentSources: {
    fontFamily: "var(--ls-font)", fontSize: 12,
    color: "var(--ls-muted-fg)",
    textAlign: "right",
    fontWeight: 500,
  },

  /* re-skinned tag/confidence */
  tagPill: {
    display: "inline-flex",
    alignItems: "center",
    height: 22,
    padding: "0 9px",
    borderRadius: 999,
    fontFamily: "var(--ls-font)",
    fontSize: 11.5,
    fontWeight: 500,
    color: "var(--ls-muted-fg)",
    background: "var(--ls-muted)",
    border: "1px solid var(--ls-border)",
    whiteSpace: "nowrap",
    letterSpacing: "-0.003em",
  },
};

function ConfidenceBarV2({ level, max = 5 }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 3 }}>
      {Array.from({ length: max }).map((_, i) => (
        <i
          key={i}
          style={{
            display: "block",
            width: 4, height: 9,
            borderRadius: 1.5,
            background: i < level
              ? (i < 2 ? "#a78bfa" : i < 4 ? "#8b5cf6" : "#6366f1")
              : "#e2e8f0",
          }}
        />
      ))}
    </span>
  );
}

function TypeGlyphV2({ type, size = 12 }) {
  return (
    <span
      style={{ display: "inline-flex", color: "var(--ls-muted-fg)" }}
      dangerouslySetInnerHTML={{ __html: window.AB_TYPE_GLYPH(type, size) }}
    />
  );
}

function ConceptComposer() {
  const data = window.AB_DATA;
  const [tab, setTab] = React.useState("ask");
  const [nav, setNav] = React.useState("ask");

  const sources = [
    { id: "ask", label: "Ask" },
    { id: "company", label: "Company" },
    { id: "market", label: "Market" },
    { id: "brief", label: "Brief" },
    { id: "url", label: "URL" },
    { id: "pdf", label: "PDF" },
    { id: "youtube", label: "YouTube" },
  ];

  const suggestions = [
    "Compare TSMC and Samsung foundry roadmap",
    "Summarize this earnings call →",
    "Find risks in my GLP-1 thesis",
    "What's changed in uranium this week?",
  ];

  return (
    <div className="ab-root concept" style={composerStyles.root}>
      <style>{`
        :where(.concept) {
          --ls-fg: #0f172a;
          --ls-muted-fg: #64748b;
          --ls-muted: #f8fafc;
          --ls-border: #e5e7eb;
          --ls-font: "Inter", "Inter Tight", -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
        }
        @keyframes ab-blink { 0%, 50% { opacity: 1 } 50.01%, 100% { opacity: 0 } }
      `}</style>

      <div style={composerStyles.bgGlow}/>

      {/* TOP NAV */}
      <div style={composerStyles.topbar}>
        <div style={composerStyles.brand}>
          <span style={composerStyles.brandMark}>A</span>
          <span>AlphaBrief</span>
        </div>

        <nav style={composerStyles.navCenter}>
          {[
            { id: "ask", label: "Ask" },
            { id: "news", label: "News" },
            { id: "reflection", label: "Reflection" },
          ].map((n) => (
            <span
              key={n.id}
              style={composerStyles.navItem(nav === n.id)}
              onClick={() => setNav(n.id)}
            >
              {n.label}
            </span>
          ))}
        </nav>

        <div style={composerStyles.topRight}>
          <span style={composerStyles.badgePill}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e" }}/>
            142 briefs
          </span>
          <span style={composerStyles.avatar}>{data.user.initials}</span>
        </div>
      </div>

      <div style={composerStyles.body}>
        <div style={composerStyles.hero}>
          <div style={composerStyles.statusPill}>
            <span style={composerStyles.statusDot}/>
            <span>Tuesday · May 04 · ready when you are</span>
          </div>

          <div style={composerStyles.prompt}>
            What would you like to{" "}
            <span style={composerStyles.promptAccent}>research</span>, Marcus?
          </div>
          <div style={composerStyles.subPrompt}>
            Drop in a company, market, URL, PDF, or video — get a structured brief
            with insights, risks, and cited sources in minutes.
          </div>

          <div style={composerStyles.inputShell}>
            <div style={composerStyles.input}>
              <span style={{ color: "var(--ls-muted-fg)" }}>
                Nvidia Blackwell ramp — what's the latest from supply-chain checks
              </span>
              <span style={composerStyles.inputCaret} />
            </div>
            <div style={composerStyles.inputBar}>
              <div style={composerStyles.sourceTabs}>
                {sources.map((s) => (
                  <div
                    key={s.id}
                    style={composerStyles.sourceTab(tab === s.id)}
                    onClick={() => setTab(s.id)}
                  >
                    {s.label}
                  </div>
                ))}
              </div>
              <button style={composerStyles.generate}>
                Generate analysis
                <span style={composerStyles.kbdLight}>⏎</span>
              </button>
            </div>
          </div>

          <div style={composerStyles.suggestRow}>
            {suggestions.map((s) => (
              <button key={s} style={composerStyles.suggest}>{s}</button>
            ))}
          </div>
        </div>

        {/* Resume drafts */}
        <div style={composerStyles.resumeStrip}>
          {data.drafts.map((d) => (
            <div key={d.id} style={composerStyles.resumeCard}>
              <div style={composerStyles.resumeLabel}>
                <span style={composerStyles.resumeDot}/>
                In progress · {d.lastEdit}
              </div>
              <div style={composerStyles.resumeTitle}>{d.title}</div>
              <div style={composerStyles.resumeMeta}>
                <span>{d.sources} sources</span>
                <span>{Math.round(d.progress * 100)}%</span>
              </div>
              <div style={composerStyles.resumeBar}>
                <div style={composerStyles.resumeBarFill(d.progress)} />
              </div>
            </div>
          ))}
        </div>

        {/* Recents */}
        <div style={composerStyles.recentsSection}>
          <div style={composerStyles.sectionHead}>
            <div>
              <div style={composerStyles.sectionTitle}>Recent briefs</div>
              <div style={{ ...composerStyles.sectionSub, marginTop: 2 }}>
                Latest analyses from your workspace
              </div>
            </div>
            <div style={composerStyles.sectionLink}>View all →</div>
          </div>
          {data.recentBriefs.slice(0, 6).map((b) => (
            <div key={b.id} style={composerStyles.recentRow}>
              <div style={composerStyles.recentDate}>{b.date}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                <TypeGlyphV2 type={b.type} />
                <div style={{ ...composerStyles.recentTitle, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {b.title}
                </div>
              </div>
              <div style={composerStyles.recentTags}>
                {b.tags.slice(0, 3).map((t) => (
                  <span key={t} style={composerStyles.tagPill}>{t}</span>
                ))}
              </div>
              <ConfidenceBarV2 level={b.confidence} />
              <div style={composerStyles.recentSources}>{b.sources} src</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

window.ConceptComposer = ConceptComposer;
window.ConfidenceBar = ConfidenceBarV2;
window.TypeGlyph = TypeGlyphV2;
