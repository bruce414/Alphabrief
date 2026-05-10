import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Icon } from "@/components/workspace/icons";
import { createProject } from "@/lib/workspaceApi";
import { ApiError } from "@/lib/api";
import { useProjects } from "@/hooks/useProjects";
import { T } from "@/styles/tokens";
import type { Project } from "@/types/workspace";

const PROJECT_KINDS = [
  "COVERAGE",
  "THESIS",
  "EVENT",
  "THEME",
  "DECISION",
] as const;

function formatUpdatedLabel(iso: string): string {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const sec = Math.floor((now - then) / 1000);
  if (sec < 45) return "just now";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day}d ago`;
  return new Date(iso).toLocaleDateString();
}

function SpaceCard({
  project,
  onEnter,
}: {
  project: Project;
  onEnter: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onEnter}
      style={{
        textAlign: "left",
        background: T.white,
        border: `1px solid ${T.border}`,
        borderRadius: 14,
        padding: "24px 26px",
        cursor: "pointer",
        transition: "box-shadow 0.15s ease, border-color 0.15s ease",
        fontFamily: T.fontSans,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.08)";
        e.currentTarget.style.borderColor = T.gray300;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.style.borderColor = T.border;
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            minWidth: 0,
          }}
        >
          <Icon.ResearchSpace style={{ flexShrink: 0 }} />
          <span
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: T.black,
              letterSpacing: "-0.01em",
            }}
          >
            {project.title}
          </span>
        </div>
        <Icon.ArrowUpRight style={{ flexShrink: 0, color: T.gray400 }} />
      </div>
      {project.description ? (
        <p
          style={{
            fontSize: 13,
            color: T.gray500,
            margin: "10px 0 16px",
            lineHeight: 1.5,
          }}
        >
          {project.description}
        </p>
      ) : null}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginTop: project.description ? 0 : 10,
          fontSize: 11,
          fontWeight: 600,
          color: T.gray400,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        <span>{project.chatCount} threads</span>
        <span>·</span>
        <span>Updated {formatUpdatedLabel(project.updatedAt)}</span>
      </div>
    </button>
  );
}

export function ResearchSpacesView() {
  const navigate = useNavigate();
  const { projects, isLoading, mutate } = useProjects();

  const researchProjects = projects.filter((p) => p.kind !== "CATCHALL");

  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newKind, setNewKind] =
    useState<(typeof PROJECT_KINDS)[number]>("COVERAGE");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const openDialog = useCallback(() => {
    setCreateError(null);
    setNewTitle("");
    setNewKind("COVERAGE");
    setDialogOpen(true);
  }, []);

  const closeDialog = useCallback(() => {
    if (creating) return;
    setDialogOpen(false);
  }, [creating]);

  const handleCreateProject = useCallback(async () => {
    const title = newTitle.trim();
    if (!title) {
      setCreateError("Title is required.");
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      await createProject({
        title,
        kind: newKind,
      });
      await mutate();
      setDialogOpen(false);
      setNewTitle("");
    } catch (e) {
      setCreateError(
        e instanceof ApiError ? e.message : "Could not create space.",
      );
    } finally {
      setCreating(false);
    }
  }, [newTitle, newKind, mutate]);

  const handleEnterSpace = useCallback(
    (project: Project) => {
      navigate(`/app/research/${project.id}`);
    },
    [navigate],
  );

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: T.bgPanel,
        fontFamily: T.fontSans,
        color: T.black,
        minHeight: 0,
      }}
    >
      <div
        style={{
          height: 52,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          borderBottom: `1px solid ${T.border}`,
          background: T.bgPanel,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 13,
            minWidth: 0,
          }}
        >
          <Icon.ResearchSpace style={{ flexShrink: 0 }} />
          <span style={{ fontWeight: 600, color: T.black }}>
            Research spaces
          </span>
          {researchProjects.length > 0 ? (
            <>
              <span style={{ color: T.gray300 }}>·</span>
              <span style={{ color: T.gray400 }}>
                {researchProjects.length} active
              </span>
            </>
          ) : null}
        </div>
        <button
          type="button"
          onClick={openDialog}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "7px 14px",
            background: T.black,
            color: T.white,
            border: "none",
            borderRadius: 10,
            cursor: "pointer",
            fontFamily: T.fontSans,
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          <Icon.Plus size={12} />
          New space
        </button>
      </div>

      <div
        style={{
          flex: 1,
          overflow: "auto",
          padding: "48px 60px",
          minHeight: 0,
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: T.gray400,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          Spaces
        </div>
        <h1
          style={{
            fontFamily: T.fontSans,
            fontSize: 48,
            fontWeight: 800,
            color: T.black,
            letterSpacing: "-0.03em",
            margin: "8px 0 12px",
            lineHeight: 1.1,
          }}
        >
          Pick a research space to enter
        </h1>
        <p
          style={{
            fontSize: 14,
            color: T.gray500,
            marginBottom: 40,
            lineHeight: 1.5,
          }}
        >
          Each space holds its own threads, sources, memory, and canvas.
        </p>

        {isLoading ? (
          <div style={{ color: T.gray400, fontSize: 14 }}>Loading spaces…</div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 16,
            }}
          >
            {researchProjects.map((project) => (
              <SpaceCard
                key={project.id}
                project={project}
                onEnter={() => handleEnterSpace(project)}
              />
            ))}
            <button
              type="button"
              onClick={openDialog}
              style={{
                textAlign: "center",
                background: "transparent",
                border: `1.5px dashed ${T.gray300}`,
                borderRadius: 14,
                padding: "40px 26px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                minHeight: 150,
                transition: "border-color 0.15s ease, background 0.15s ease",
                fontFamily: T.fontSans,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = T.gray100;
                e.currentTarget.style.borderColor = T.gray400;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.borderColor = T.gray300;
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: "50%",
                  background: "rgba(180,175,168,0.18)",
                  backdropFilter: "blur(6px)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: T.gray400,
                }}
              >
                <Icon.Plus size={22} />
              </div>
            </button>
          </div>
        )}
      </div>

      {dialogOpen ? (
        <div
          role="presentation"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: 24,
          }}
          onClick={closeDialog}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="new-space-title"
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
              id="new-space-title"
              style={{
                fontSize: 18,
                fontWeight: 700,
                color: T.black,
                marginBottom: 20,
              }}
            >
              New research space
            </h2>
            <label
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: T.gray500,
                marginBottom: 6,
              }}
            >
              Title
            </label>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. AI Infra · 2026"
              autoFocus
              disabled={creating}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: 8,
                border: `1px solid ${T.border}`,
                fontFamily: T.fontSans,
                fontSize: 14,
                marginBottom: 16,
                boxSizing: "border-box",
              }}
            />
            <label
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: T.gray500,
                marginBottom: 6,
              }}
            >
              Kind
            </label>
            <select
              value={newKind}
              onChange={(e) =>
                setNewKind(e.target.value as (typeof PROJECT_KINDS)[number])
              }
              disabled={creating}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: 8,
                border: `1px solid ${T.border}`,
                fontFamily: T.fontSans,
                fontSize: 14,
                marginBottom: 16,
                background: T.white,
                cursor: creating ? "not-allowed" : "pointer",
                boxSizing: "border-box",
              }}
            >
              {PROJECT_KINDS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
            {createError ? (
              <p style={{ color: "#b42318", fontSize: 13, marginBottom: 12 }}>
                {createError}
              </p>
            ) : null}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 10,
                marginTop: 8,
              }}
            >
              <button
                type="button"
                onClick={closeDialog}
                disabled={creating}
                style={{
                  padding: "8px 16px",
                  borderRadius: 8,
                  border: `1px solid ${T.border}`,
                  background: T.white,
                  cursor: creating ? "not-allowed" : "pointer",
                  fontFamily: T.fontSans,
                  fontSize: 13,
                  fontWeight: 500,
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleCreateProject()}
                disabled={creating}
                style={{
                  padding: "8px 16px",
                  borderRadius: 8,
                  border: "none",
                  background: T.black,
                  color: T.white,
                  cursor: creating ? "not-allowed" : "pointer",
                  fontFamily: T.fontSans,
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {creating ? "Creating…" : "Create"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
