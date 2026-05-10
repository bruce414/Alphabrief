import { AlphaBriefLogo } from "@/components/workspace/logo";
import { Icon } from "@/components/workspace/icons";
import { useChats } from "@/hooks/useChats";
import { useProjectSources } from "@/hooks/useProjectSources";
import { T } from "@/styles/tokens";
import type { Chat, Project } from "@/types/workspace";

export type SpaceSidebarTab = "canvas" | "sources" | "memory";

function formatRelativeTime(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  const now = Date.now();
  const sec = Math.floor((now - then) / 1000);
  if (sec < 60) return "Just now";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day}d`;
  return new Date(iso).toLocaleDateString();
}

function sortChatsByRecent(items: Chat[]): Chat[] {
  return [...items].sort((a, b) => {
    const ta = a.lastTurnAt ? new Date(a.lastTurnAt).getTime() : 0;
    const tb = b.lastTurnAt ? new Date(b.lastTurnAt).getTime() : 0;
    return tb - ta;
  });
}

export type SpaceSidebarProps = {
  project: Project;
  activeTab: SpaceSidebarTab;
  onTabChange: (tab: SpaceSidebarTab) => void;
  onBack: () => void;
};

const tabs: {
  id: SpaceSidebarTab;
  label: string;
  Icon: (typeof Icon)["Canvas"];
}[] = [
    { id: "canvas", label: "Canvas", Icon: Icon.Canvas },
    { id: "sources", label: "Sources", Icon: Icon.Sources },
    { id: "memory", label: "Memory", Icon: Icon.Memory },
  ];

export function SpaceSidebar({
  project,
  activeTab,
  onTabChange,
  onBack,
}: SpaceSidebarProps) {
  const { sources } = useProjectSources(project.id);
  const { chats } = useChats(project.id);
  const orderedChats = sortChatsByRecent(chats);

  return (
    <aside
      style={{
        width: 280,
        minWidth: 280,
        background: T.sidebar,
        borderRight: `1px solid ${T.border}`,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        fontFamily: T.fontSans,
        color: T.black,
      }}
    >
      {/* Top bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "14px 16px",
          borderBottom: `1px solid ${T.border}`,
          flexShrink: 0,
        }}
      >
        <button
          type="button"
          onClick={onBack}
          aria-label="Back to research spaces"
          style={{
            width: 36,
            height: 36,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: "none",
            background: "transparent",
            cursor: "pointer",
            color: T.black,
            borderRadius: 8,
          }}
        >
          <Icon.Back />
        </button>
        <div
          style={{
            flex: 1,
            display: "flex",
            justifyContent: "center",
            minWidth: 0,
          }}
        >
          <AlphaBriefLogo size={22} />
        </div>
        <button
          type="button"
          aria-label="Toggle sidebar"
          style={{
            width: 36,
            height: 36,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: "none",
            background: "transparent",
            cursor: "default",
            color: T.black,
            borderRadius: 8,
          }}
        >
          <Icon.Sidebar />
        </button>
      </div>

      {/* Space info */}
      <div style={{ padding: "20px 20px 16px", flexShrink: 0 }}>
        <div
          style={{
            fontSize: 10,
            fontWeight: 600,
            color: T.gray400,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: 8,
          }}
        >
          Research space
        </div>
        <div
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: T.black,
            letterSpacing: "-0.02em",
            lineHeight: 1.2,
            marginBottom: 8,
          }}
        >
          {project.title}
        </div>
        {project.description ? (
          <div
            style={{
              fontSize: 12,
              color: T.gray500,
              lineHeight: 1.5,
            }}
          >
            {project.description}
          </div>
        ) : null}
      </div>

      {/* Tab nav */}
      <nav style={{ flexShrink: 0 }}>
        {tabs.map(({ id, label, Icon: TabIcon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onTabChange(id)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "9px 20px",
                border: "none",
                borderRadius: 0,
                background: active ? T.gray200 : "transparent",
                cursor: "pointer",
                fontFamily: T.fontSans,
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                color: T.black,
                textAlign: "left",
              }}
            >
              <TabIcon
                style={{
                  flexShrink: 0,
                  color: active ? T.black : T.gray400,
                }}
              />
              {label}
            </button>
          );
        })}
      </nav>

      <div
        style={{
          height: 1,
          background: T.border,
          margin: "12px 0",
          flexShrink: 0,
        }}
      />

      {/* Body */}
      <div
        style={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          padding: "0 0 12px",
        }}
      >
        {activeTab === "canvas" ? (
          <>
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: T.gray400,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                padding: "0 20px 8px",
              }}
            >
              Resources
            </div>
            <div style={{ padding: "0 12px" }}>
              {sources.slice(0, 8).map((source) => {
                const title = source.title?.trim() || "Untitled";
                return (
                  <div
                    key={source.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      padding: "6px 8px",
                    }}
                  >
                    <Icon.Sources
                      style={{ flexShrink: 0, color: T.gray400 }}
                      width={14}
                      height={14}
                    />
                    <span
                      title={title}
                      style={{
                        fontSize: 12,
                        color: T.gray600,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        minWidth: 0,
                        flex: 1,
                      }}
                    >
                      {title}
                    </span>
                  </div>
                );
              })}
            </div>

            <div
              style={{
                height: 1,
                background: T.border,
                margin: "12px 0",
              }}
            />

            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: T.gray400,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                padding: "0 20px 8px",
              }}
            >
              Chats
            </div>
            <div style={{ padding: "0 12px" }}>
              {orderedChats.map((chat) => (
                <div
                  key={chat.id}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 8,
                    padding: "6px 8px",
                  }}
                >
                  <Icon.Chat
                    style={{
                      flexShrink: 0,
                      marginTop: 2,
                      color: T.gray400,
                    }}
                  />
                  <span style={{ flex: 1, minWidth: 0 }}>
                    <span
                      style={{
                        display: "block",
                        fontSize: 13,
                        fontWeight: 500,
                        color: T.black,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {chat.title}
                    </span>
                    <span
                      style={{
                        display: "block",
                        fontSize: 11,
                        color: T.gray500,
                        marginTop: 2,
                      }}
                    >
                      {formatRelativeTime(chat.lastTurnAt)}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </>
        ) : activeTab === "sources" ? (
          <div
            style={{
              padding: "8px 20px",
              fontSize: 13,
              color: T.gray500,
              lineHeight: 1.5,
            }}
          >
            Sources panel — build in a later prompt
          </div>
        ) : (
          <div
            style={{
              padding: "8px 20px",
              fontSize: 13,
              color: T.gray500,
              lineHeight: 1.5,
            }}
          >
            Memory panel — build in a later prompt
          </div>
        )}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: "12px 20px",
          borderTop: `1px solid ${T.border}`,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 14,
          }}
        >
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: "50%",
              background: T.gray300,
              color: T.black,
              fontSize: 11,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            BZ
          </div>
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: T.black,
                lineHeight: 1.2,
              }}
            >
              Bruce Zhang
            </div>
            <div
              style={{
                fontSize: 10,
                color: T.gray500,
                marginTop: 2,
              }}
            >
              Pro
            </div>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          {(
            [
              { IconBtn: Icon.Brief, label: "Brief" },
              { IconBtn: Icon.Pin, label: "Pin" },
              { IconBtn: Icon.Share, label: "Share" },
            ] as const
          ).map(({ IconBtn, label }) => (
            <button
              key={label}
              type="button"
              disabled
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 4,
                padding: "8px 0",
                border: "none",
                background: "transparent",
                cursor: "not-allowed",
                opacity: 0.75,
                fontFamily: T.fontSans,
                color: T.gray500,
              }}
            >
              <IconBtn width={16} height={16} />
              <span style={{ fontSize: 10, color: T.gray500 }}>{label}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
