import { useState, type CSSProperties } from "react";

import { useProjectOverview } from "@/hooks/useProjectOverview";
import { runUpdateCheck } from "@/lib/checkUpdates";
import { T } from "@/styles/tokens";
import type { Project, ProjectOverview } from "@/types/workspace";

const COMING_SOON = "Editing coming soon";

const cardStyle: CSSProperties = {
  background: T.white,
  border: `1px solid ${T.border}`,
  borderRadius: 12,
  padding: "20px 24px",
  marginBottom: 16,
};

const scopeRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: 16,
  padding: "12px 0",
  borderBottom: `1px solid ${T.border}`,
};

const scopeLabelStyle: CSSProperties = {
  width: 132,
  flexShrink: 0,
  fontSize: 12,
  fontWeight: 600,
  color: T.gray500,
  paddingTop: 2,
};

const panelShellStyle: CSSProperties = {
  flex: 1,
  minHeight: 0,
  overflow: "auto",
  padding: "24px 28px",
  fontFamily: T.fontSans,
  background: T.workspaceDashboard,
};

const panelInnerStyle: CSSProperties = {
  maxWidth: 960,
  margin: "0 auto",
};

function formatOverviewDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function noopEdit() {
  /* Slice 2 — editing UI */
}

function ghostButtonStyle(): CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    fontSize: 11,
    fontWeight: 500,
    color: T.gray600,
    border: `1px solid ${T.border}`,
    borderRadius: 8,
    padding: "4px 10px",
    cursor: "pointer",
    background: T.white,
    fontFamily: T.fontSans,
  };
}

function Pill({ label }: { label: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: 11,
        fontWeight: 500,
        color: T.black,
        background: T.gray100,
        border: `1px solid ${T.border}`,
        borderRadius: 999,
        padding: "4px 10px",
        lineHeight: 1.2,
      }}
    >
      {label}
    </span>
  );
}

function AddButton() {
  return (
    <button
      type="button"
      title={COMING_SOON}
      onClick={noopEdit}
      style={ghostButtonStyle()}
    >
      + Add
    </button>
  );
}

function ScopeRow({
  label,
  chips,
  textValue,
}: {
  label: string;
  chips?: string[];
  textValue?: string | null;
}) {
  const hasChips = chips !== undefined;
  const items = chips ?? [];
  const hasText = textValue != null && textValue.trim() !== "";
  const empty = hasChips ? items.length === 0 : !hasText;

  return (
    <div style={scopeRowStyle}>
      <div style={scopeLabelStyle}>{label}</div>
      <div
        style={{
          flex: 1,
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: 8,
          minWidth: 0,
        }}
      >
        {empty ? (
          <span style={{ fontSize: 13, color: T.gray400 }}>—</span>
        ) : hasChips ? (
          items.map((item) => <Pill key={item} label={item} />)
        ) : (
          <span style={{ fontSize: 13, color: T.black }}>{textValue}</span>
        )}
      </div>
      <AddButton />
    </div>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <span style={{ fontSize: 11, color: T.gray500 }}>
      <span style={{ color: T.gray400 }}>{label}</span> {value}
    </span>
  );
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div
      style={{
        padding: "14px 16px",
        borderRadius: 10,
        border: `1px solid ${T.border}`,
        background: T.gray100,
      }}
    >
      <div
        style={{
          fontSize: 22,
          fontWeight: 700,
          color: T.black,
          letterSpacing: "-0.02em",
          lineHeight: 1.1,
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: 11,
          color: T.gray500,
          marginTop: 6,
          fontWeight: 500,
        }}
      >
        {label}
      </div>
    </div>
  );
}

function OverviewContent({
  overview,
  project,
  onRunUpdateCheck,
  isChecking,
}: {
  overview: ProjectOverview;
  project: Project;
  onRunUpdateCheck: () => void;
  isChecking: boolean;
}) {
  const title = overview.title || project.title;
  const description = overview.description ?? project.description;
  const updates = overview.status.updatesAvailableCount;

  return (
    <>
      <section style={cardStyle}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 16,
            marginBottom: description || overview.researchGoal ? 12 : 0,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1
              style={{
                fontSize: 22,
                fontWeight: 700,
                color: T.black,
                margin: "0 0 8px",
                letterSpacing: "-0.02em",
                lineHeight: 1.2,
              }}
            >
              {title}
            </h1>
            {description ? (
              <p
                style={{
                  fontSize: 13,
                  color: T.gray500,
                  margin: 0,
                  lineHeight: 1.55,
                }}
              >
                {description}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            title={COMING_SOON}
            onClick={noopEdit}
            style={{
              ...ghostButtonStyle(),
              flexShrink: 0,
              padding: "6px 12px",
            }}
          >
            Edit details
          </button>
        </div>

        {overview.researchGoal ? (
          <div
            style={{
              fontSize: 12,
              color: T.gray600,
              lineHeight: 1.55,
              padding: "12px 14px",
              background: T.gray100,
              borderRadius: 8,
              border: `1px solid ${T.border}`,
              marginBottom: 16,
            }}
          >
            {overview.researchGoal}
          </div>
        ) : null}

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: "10px 20px",
          }}
        >
          <MetaItem label="Created" value={formatOverviewDate(overview.createdAt)} />
          <MetaItem label="Last active" value={formatOverviewDate(overview.updatedAt)} />
          <MetaItem
            label="Last checked"
            value={formatOverviewDate(overview.status.lastCheckedAt)}
          />
          {updates > 0 ? (
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: T.black,
                background: T.gray100,
                border: `1px solid ${T.border}`,
                borderRadius: 999,
                padding: "3px 10px",
              }}
            >
              • {updates} update{updates === 1 ? "" : "s"} available
            </span>
          ) : null}
        </div>
      </section>

      <section style={cardStyle}>
        <h2
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: T.black,
            margin: "0 0 4px",
            letterSpacing: "-0.02em",
          }}
        >
          Research scope
        </h2>
        <ScopeRow label="Included topics" chips={overview.includedTopics} />
        <ScopeRow label="Excluded topics" chips={overview.excludedTopics} />
        <ScopeRow label="Target entities" chips={overview.targetEntities} />
        <ScopeRow label="Time horizon" textValue={overview.timeHorizon} />
      </section>

      <section style={{ ...cardStyle, marginBottom: 0 }}>
        <h2
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: T.black,
            margin: "0 0 16px",
            letterSpacing: "-0.02em",
          }}
        >
          Status
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
            gap: 12,
            marginBottom: 16,
          }}
        >
          <StatTile label="Canvas nodes" value={overview.status.totalNodes} />
          <StatTile label="Sources" value={overview.status.totalSources} />
          <StatTile
            label="Open questions"
            value={overview.status.openQuestionsCount}
          />
          <StatTile
            label="Updates available"
            value={overview.status.updatesAvailableCount}
          />
        </div>
        <button
          type="button"
          onClick={onRunUpdateCheck}
          disabled={isChecking}
          style={{
            ...ghostButtonStyle(),
            fontSize: 12,
            padding: "8px 14px",
            fontWeight: 600,
            color: T.black,
            cursor: isChecking ? "wait" : "pointer",
            opacity: isChecking ? 0.7 : 1,
          }}
        >
          {isChecking ? "Checking…" : "Run update check"}
        </button>
      </section>
    </>
  );
}

export function WorkspaceOverviewPanel({ project }: { project: Project }) {
  const { overview, mutate, isLoading, error } = useProjectOverview(project.id);
  const [isChecking, setIsChecking] = useState(false);

  const handleRunUpdateCheck = () => {
    if (isChecking) return;
    setIsChecking(true);
    void runUpdateCheck(project.id)
      .then((next) => mutate(next, { revalidate: false }))
      .catch((e) => console.error("Update check failed", e))
      .finally(() => setIsChecking(false));
  };

  return (
    <div style={panelShellStyle}>
      <div style={panelInnerStyle}>
        {isLoading ? (
          <div style={{ fontSize: 13, color: T.gray400 }}>Loading overview…</div>
        ) : error ? (
          <div style={{ fontSize: 13, color: T.red500 }}>
            Could not load overview.
          </div>
        ) : overview ? (
          <OverviewContent
            overview={overview}
            project={project}
            onRunUpdateCheck={handleRunUpdateCheck}
            isChecking={isChecking}
          />
        ) : (
          <div style={{ fontSize: 13, color: T.gray400 }}>
            Overview unavailable.
          </div>
        )}
      </div>
    </div>
  );
}
