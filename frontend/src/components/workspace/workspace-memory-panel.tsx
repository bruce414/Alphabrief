import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

import { useProjectMemory } from "@/hooks/useProjectMemory";
import { ApiError } from "@/lib/api";
import { patchProjectMemory } from "@/lib/workspaceApi";
import { T } from "@/styles/tokens";

type MemorySection = "summary" | "entities" | "themes" | "openQuestions";

export function WorkspaceMemoryPanel({ projectId }: { projectId: string }) {
  const { memory, mutate: mutateMemory, isLoading, isRefreshing, refresh } =
    useProjectMemory(projectId);

  const [editingSection, setEditingSection] = useState<MemorySection | null>(
    null,
  );
  const [draft, setDraft] = useState("");
  const [isSavingMemory, setIsSavingMemory] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [showRefreshSuccess, setShowRefreshSuccess] = useState(false);
  const [refreshInfo, setRefreshInfo] = useState<string | null>(null);
  const flashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    };
  }, []);

  function clearFlashTimer() {
    if (flashTimerRef.current) {
      clearTimeout(flashTimerRef.current);
      flashTimerRef.current = null;
    }
  }

  async function handleRefreshWithAi() {
    setRefreshError(null);
    setRefreshInfo(null);
    setShowRefreshSuccess(false);
    clearFlashTimer();
    try {
      const result = await refresh();
      if (result.status === "NO_ACTIVITY") {
        setRefreshInfo("No recent activity to summarize yet.");
        flashTimerRef.current = setTimeout(() => {
          setRefreshInfo(null);
          flashTimerRef.current = null;
        }, 2500);
        return;
      }
      setShowRefreshSuccess(true);
      flashTimerRef.current = setTimeout(() => {
        setShowRefreshSuccess(false);
        flashTimerRef.current = null;
      }, 2000);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Something went wrong";
      setRefreshError(msg);
    }
  }

  const memoryText = useMemo(() => {
    if (!memory) {
      return {
        summary: "",
        entities: "",
        themes: "",
        openQuestions: "",
      };
    }
    return {
      summary: memory.summaryMarkdown ?? "",
      entities: (memory.entities ?? []).join(", "),
      themes: (memory.themes ?? []).join(", "),
      openQuestions: (memory.openQuestions ?? []).join("\n"),
    };
  }, [memory]);

  async function saveMemorySection(section: MemorySection, text: string) {
    setIsSavingMemory(true);
    try {
      const body: Record<string, unknown> = {};
      if (section === "summary") {
        body.summaryMarkdown = text;
      } else if (section === "entities") {
        body.entities = text
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      } else if (section === "themes") {
        body.themes = text
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      } else if (section === "openQuestions") {
        body.openQuestions = text
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean);
      }
      await patchProjectMemory(projectId, body);
      await mutateMemory();
      setEditingSection(null);
    } finally {
      setIsSavingMemory(false);
    }
  }

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        overflow: "auto",
        padding: "24px 28px",
        fontFamily: T.fontSans,
        background: T.workspaceDashboard,
      }}
    >
      <style>{`
        .memory-panel-md {
          font-size: 12px;
          line-height: 1.65;
          color: ${T.gray600};
          word-break: break-word;
        }
        .memory-panel-md > *:first-child { margin-top: 0; }
        .memory-panel-md > *:last-child { margin-bottom: 0; }
        .memory-panel-md p { margin: 0 0 0.75em; }
        .memory-panel-md h1,
        .memory-panel-md h2,
        .memory-panel-md h3 {
          font-weight: 700;
          color: ${T.black};
          line-height: 1.3;
          margin: 1em 0 0.45em;
        }
        .memory-panel-md h1 { font-size: 17px; }
        .memory-panel-md h2 { font-size: 15px; }
        .memory-panel-md h3 { font-size: 13px; }
        .memory-panel-md ul,
        .memory-panel-md ol {
          margin: 0 0 0.75em;
          padding-left: 1.25em;
        }
        .memory-panel-md li { margin: 0.2em 0; }
        .memory-panel-md strong { font-weight: 700; color: ${T.black}; }
        .memory-panel-md em { font-style: italic; }
        .memory-panel-md a {
          color: ${T.black};
          text-decoration: underline;
          text-underline-offset: 2px;
        }
        .memory-panel-md blockquote {
          margin: 0.5em 0 0.75em;
          padding: 0.15em 0 0.15em 12px;
          border-left: 3px solid ${T.gray200};
          color: ${T.gray600};
        }
        .memory-panel-md code {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          font-size: 0.9em;
          background: ${T.gray100};
          border: 1px solid ${T.border};
          border-radius: 4px;
          padding: 1px 4px;
        }
      `}</style>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <h2
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: T.black,
            margin: 0,
            letterSpacing: "-0.02em",
          }}
        >
          Memory
        </h2>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {showRefreshSuccess ? (
            <span
              style={{
                fontSize: 11,
                color: T.gray500,
                fontFamily: T.fontSans,
              }}
              aria-live="polite"
            >
              Updated
            </span>
          ) : null}
          <button
            type="button"
            onClick={() => void handleRefreshWithAi()}
            disabled={isLoading || isRefreshing}
            title="Refresh memory from recent chat activity"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              fontSize: 11,
              fontWeight: 500,
              color: T.gray600,
              border: `1px solid ${T.border}`,
              borderRadius: 8,
              padding: "5px 10px",
              cursor:
                isLoading || isRefreshing ? "default" : "pointer",
              background: T.white,
              fontFamily: T.fontSans,
              opacity: isLoading || isRefreshing ? 0.75 : 1,
            }}
          >
            {isRefreshing ? (
              <span
                aria-hidden
                style={{
                  width: 12,
                  height: 12,
                  border: `2px solid ${T.gray200}`,
                  borderTopColor: T.gray500,
                  borderRadius: "50%",
                  display: "inline-block",
                  flexShrink: 0,
                  animation: "ab-spin 0.65s linear infinite",
                }}
              />
            ) : (
              <span
                aria-hidden
                style={{
                  fontSize: 12,
                  lineHeight: 1,
                  color: T.gray500,
                }}
              >
                ↻
              </span>
            )}
            Refresh with AI
          </button>
        </div>
      </div>

      <style>{`
        @keyframes ab-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>

      {refreshError ? (
        <div
          role="alert"
          style={{
            fontSize: 12,
            color: T.gray600,
            marginBottom: 12,
            padding: "8px 10px",
            borderRadius: 8,
            border: `1px solid ${T.border}`,
            background: T.gray100,
            fontFamily: T.fontSans,
          }}
        >
          {refreshError}
        </div>
      ) : null}
      {refreshInfo ? (
        <div
          style={{
            fontSize: 12,
            color: T.gray500,
            marginBottom: 12,
            fontFamily: T.fontSans,
          }}
        >
          {refreshInfo}
        </div>
      ) : null}

      {isLoading ? (
        <div style={{ fontSize: 13, color: T.gray400 }}>Loading memory…</div>
      ) : !memory ? (
        <div
          style={{
            fontSize: 12,
            color: T.gray400,
            fontFamily: T.fontSans,
          }}
        >
          Memory builds as you research. Add a note to start.
        </div>
      ) : (
        <div style={{ paddingBottom: 12 }}>
          {(
            [
              { id: "summary", title: "Summary", value: memoryText.summary },
              {
                id: "entities",
                title: "Entities",
                value: memoryText.entities,
              },
              { id: "themes", title: "Themes", value: memoryText.themes },
              {
                id: "openQuestions",
                title: "Open Questions",
                value: memoryText.openQuestions,
              },
            ] as const
          ).map(({ id, title, value }) => {
            const isEditing = editingSection === id;
            return (
              <div key={id} style={{ padding: "10px 0" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    justifyContent: "space-between",
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <div
                    style={{
                      fontSize: 10,
                      color: T.gray400,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      fontWeight: 600,
                    }}
                  >
                    {title}
                  </div>
                  {isEditing ? (
                    <button
                      type="button"
                      onClick={() => saveMemorySection(id, draft)}
                      disabled={isSavingMemory}
                      style={{
                        fontSize: 11,
                        color: T.gray400,
                        fontFamily: T.fontSans,
                        border: "none",
                        background: "transparent",
                        cursor: isSavingMemory ? "default" : "pointer",
                        padding: 0,
                      }}
                    >
                      Save
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setEditingSection(id);
                        setDraft(value);
                      }}
                      style={{
                        fontSize: 11,
                        color: T.gray400,
                        fontFamily: T.fontSans,
                        border: "none",
                        background: "transparent",
                        cursor: "pointer",
                        padding: 0,
                      }}
                    >
                      Edit
                    </button>
                  )}
                </div>

                {isEditing ? (
                  <textarea
                    value={draft}
                    autoFocus
                    onChange={(e) => setDraft(e.target.value)}
                    onBlur={() => {
                      void saveMemorySection(id, draft);
                    }}
                    style={{
                      width: "100%",
                      minHeight: 70,
                      resize: "vertical",
                      fontSize: 12,
                      color: T.gray600,
                      lineHeight: 1.5,
                      fontFamily: T.fontSans,
                      border: `1px solid ${T.border}`,
                      borderRadius: 8,
                      padding: "8px 10px",
                      background: T.white,
                      outline: "none",
                    }}
                  />
                ) : id === "summary" && (value || "").trim() ? (
                  <div className="memory-panel-md">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeSanitize]}
                    >
                      {value}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div
                    style={{
                      fontSize: 12,
                      color: T.gray600,
                      lineHeight: 1.5,
                      whiteSpace:
                        id === "openQuestions" ? "pre-wrap" : "normal",
                    }}
                  >
                    {value || ""}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
