import { Icon } from "@/components/workspace/icons";
import { useProjectSources } from "@/hooks/useProjectSources";
import { T } from "@/styles/tokens";

export function WorkspaceSourcesPanel({ projectId }: { projectId: string }) {
  const { sources, isLoading } = useProjectSources(projectId);

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
        Sources
      </h2>
      {isLoading ? (
        <div style={{ fontSize: 13, color: T.gray400 }}>Loading sources…</div>
      ) : sources.length === 0 ? (
        <div
          style={{
            fontSize: 12,
            color: T.gray400,
            fontFamily: T.fontSans,
            padding: "16px 0",
          }}
        >
          No sources yet. Paste a URL in the chat.
        </div>
      ) : (
        sources.map((source) => (
          <div
            key={source.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 0",
              cursor: "default",
            }}
          >
            <Icon.Sources style={{ color: T.gray400 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 12,
                  color: T.gray600,
                  fontFamily: T.fontSans,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
                title={
                  source.title ||
                  source.normalizedUrl ||
                  "Untitled source"
                }
              >
                {source.title ||
                  source.normalizedUrl ||
                  "Untitled source"}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: T.gray400,
                  marginTop: 2,
                }}
              >
                {source.sourceType} · {source.sourceAccessStatus}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
