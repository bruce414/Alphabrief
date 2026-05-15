import { useState } from "react";

import { AlphaBriefLogo } from "@/components/workspace/logo";
import type { CanvasQuickCreateKind } from "@/components/workspace/infinite-canvas";
import { Icon } from "@/components/workspace/icons";
import { useChats } from "@/hooks/useChats";
import { sortChatsByRecent } from "@/lib/chatSort";
import { T } from "@/styles/tokens";
import type { Project } from "@/types/workspace";

export type SpaceSidebarTab = "canvas" | "sources" | "memory";

export type CanvasSidebarCreateKind = Extract<
  CanvasQuickCreateKind,
  "STICKY_NOTE" | "MINDMAP_NODE" | "GROUP"
>;

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

export type SpaceSidebarProps = {
  project: Project;
  activeTab: SpaceSidebarTab;
  onTabChange: (tab: SpaceSidebarTab) => void;
  onBack: () => void;
  /** Highlights the active chat row (dashboard screenshot) */
  selectedChatId?: string | null;
  onSelectChat?: (chatId: string) => void;
  /** Add canvas elements (same behavior as canvas surface; previews below). */
  onCreateCanvasElement?: (kind: CanvasSidebarCreateKind) => void;
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
  selectedChatId = null,
  onSelectChat,
  onCreateCanvasElement,
}: SpaceSidebarProps) {
  const { chats } = useChats(project.id);
  const orderedChats = sortChatsByRecent(chats);
  const [toolsetsOpen, setToolsetsOpen] = useState(true);

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
                background: active ? T.gray100 : "transparent",
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

      {/* Body: Resources + Chats — fixed; tab selection drives the main canvas */}
      <div
        style={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          padding: "0 0 12px",
        }}
      >
        <button
          type="button"
          onClick={() => setToolsetsOpen((o) => !o)}
          aria-expanded={toolsetsOpen}
          aria-controls="space-sidebar-toolsets"
          id="space-sidebar-toolsets-toggle"
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 8,
            padding: "6px 20px 8px",
            border: "none",
            background: "transparent",
            cursor: "pointer",
            fontFamily: T.fontSans,
            textAlign: "left",
            borderRadius: 0,
          }}
        >
          <span
            style={{
              fontSize: 10,
              fontWeight: 600,
              color: T.gray400,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Toolsets
          </span>
          <Icon.ChevronDown
            width={14}
            height={14}
            style={{
              flexShrink: 0,
              color: T.gray500,
              transform: toolsetsOpen ? "rotate(0deg)" : "rotate(-90deg)",
              transition: "transform 0.15s ease",
            }}
            aria-hidden
          />
        </button>
        {toolsetsOpen ? (
          <div
            id="space-sidebar-toolsets"
            role="region"
            aria-labelledby="space-sidebar-toolsets-toggle"
            style={{
              padding: "0 14px",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            {(
              [
                {
                  kind: "STICKY_NOTE" as const,
                  label: "Sticky note",
                  Preview: () => (
                    <div
                      aria-hidden
                      style={{
                        width: 88,
                        height: 52,
                        borderRadius: 6,
                        background: "#fff8c5",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.12)",
                        alignSelf: "center",
                      }}
                    />
                  ),
                },
                {
                  kind: "MINDMAP_NODE" as const,
                  label: "Mindmap node",
                  Preview: () => (
                    <div
                      aria-hidden
                      style={{
                        width: 100,
                        height: 44,
                        borderRadius: 22,
                        background: T.white,
                        border: `1px solid ${T.border}`,
                        boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
                        alignSelf: "center",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 10,
                        fontWeight: 600,
                        color: T.gray500,
                      }}
                    >
                      Topic
                    </div>
                  ),
                },
                {
                  kind: "GROUP" as const,
                  label: "Group",
                  Preview: () => (
                    <div
                      aria-hidden
                      style={{
                        width: 100,
                        height: 64,
                        borderRadius: 8,
                        border: `2px dashed ${T.gray300}`,
                        background: "transparent",
                        alignSelf: "center",
                        overflow: "hidden",
                        display: "flex",
                        flexDirection: "column",
                      }}
                    >
                      <div
                        style={{
                          fontSize: 9,
                          fontWeight: 600,
                          color: T.gray500,
                          padding: "5px 8px",
                          borderBottom: `1px dashed ${T.gray300}`,
                          background: "rgba(255,255,255,0.5)",
                        }}
                      >
                        Group
                      </div>
                    </div>
                  ),
                },
              ] as const
            ).map(({ kind, label, Preview }) => (
              <button
                key={kind}
                type="button"
                disabled={!onCreateCanvasElement}
                onClick={() => onCreateCanvasElement?.(kind)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "stretch",
                  gap: 8,
                  padding: "10px 10px 12px",
                  borderRadius: 10,
                  border: `1px solid ${T.border}`,
                  background: T.white,
                  cursor: onCreateCanvasElement ? "pointer" : "not-allowed",
                  opacity: onCreateCanvasElement ? 1 : 0.55,
                  fontFamily: T.fontSans,
                  textAlign: "center",
                }}
              >
                <Preview />
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: T.black,
                  }}
                >
                  {label}
                </span>
              </button>
            ))}
          </div>
        ) : null}

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
          {orderedChats.map((chat) => {
            const selected = selectedChatId === chat.id;
            return (
              <button
                key={chat.id}
                type="button"
                onClick={() => onSelectChat?.(chat.id)}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 8,
                  padding: "8px 10px",
                  marginBottom: 4,
                  borderRadius: 8,
                  background: selected ? T.gray100 : "transparent",
                  border: "none",
                  width: "100%",
                  cursor: onSelectChat ? "pointer" : "default",
                  textAlign: "left",
                  fontFamily: T.fontSans,
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
              </button>
            );
          })}
        </div>
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
            flexDirection: "row",
            justifyContent: "space-between",
            gap: 8,
            marginBottom: 12,
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
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 4,
                padding: "8px 4px",
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

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 10,
            marginBottom: 14,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: "50%",
                background: T.black,
                color: T.white,
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
          <button
            type="button"
            aria-label="Settings"
            disabled
            style={{
              border: "none",
              background: "transparent",
              cursor: "not-allowed",
              opacity: 0.55,
              padding: 6,
              borderRadius: 8,
              color: T.gray400,
              display: "flex",
            }}
          >
            <Icon.Settings />
          </button>
        </div>
      </div>
    </aside>
  );
}
