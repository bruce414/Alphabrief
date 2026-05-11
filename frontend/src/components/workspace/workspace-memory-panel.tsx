import { useMemo, useState } from "react";

import { useProjectMemory } from "@/hooks/useProjectMemory";
import { patchProjectMemory } from "@/lib/workspaceApi";
import { T } from "@/styles/tokens";

type MemorySection = "summary" | "entities" | "themes" | "openQuestions";

export function WorkspaceMemoryPanel({ projectId }: { projectId: string }) {
  const { memory, mutate: mutateMemory, isLoading } =
    useProjectMemory(projectId);

  const [editingSection, setEditingSection] = useState<MemorySection | null>(
    null,
  );
  const [draft, setDraft] = useState("");
  const [isSavingMemory, setIsSavingMemory] = useState(false);

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
      <h2
        style={{
          fontSize: 14,
          fontWeight: 600,
          color: T.black,
          margin: "0 0 16px",
          letterSpacing: "-0.02em",
        }}
      >
        Memory
      </h2>

      <div style={{ padding: "0 0 14px" }}>
        <button
          type="button"
          disabled
          title="Coming soon"
          style={{
            fontSize: 11,
            color: T.gray400,
            border: `1px solid ${T.border}`,
            borderRadius: 8,
            padding: "4px 10px",
            cursor: "not-allowed",
            opacity: 0.5,
            background: "transparent",
            fontFamily: T.fontSans,
          }}
        >
          Refresh from activity
        </button>
      </div>

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
