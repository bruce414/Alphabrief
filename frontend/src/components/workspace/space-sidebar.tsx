import { useState, type CSSProperties } from "react";

import { AlphaBriefLogo } from "@/components/workspace/logo";
import type { CanvasQuickCreateKind } from "@/components/workspace/infinite-canvas";
import { Icon } from "@/components/workspace/icons";
import { useChats } from "@/hooks/useChats";
import { sortChatsByRecent } from "@/lib/chatSort";
import { formatRelativeTime } from "@/lib/relativeTime";
import { T } from "@/styles/tokens";
import type { Project } from "@/types/workspace";

export type SpaceSidebarTab = "overview" | "canvas" | "sources" | "memory";

export type CanvasSidebarCreateKind = Extract<
  CanvasQuickCreateKind,
  "STICKY_NOTE" | "MINDMAP_NODE" | "GROUP"
>;

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

const SIDEBAR_WIDTH_EXPANDED = 280;
const SIDEBAR_WIDTH_COLLAPSED = 56;

const tabs: {
  id: SpaceSidebarTab;
  label: string;
  Icon: (typeof Icon)["Canvas"];
}[] = [
  { id: "overview", label: "Overview", Icon: Icon.Overview },
  { id: "canvas", label: "Canvas", Icon: Icon.Canvas },
  { id: "sources", label: "Sources", Icon: Icon.Sources },
  { id: "memory", label: "Memory", Icon: Icon.Memory },
];

const iconButtonBase: CSSProperties = {
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
};

function UserProfileAvatar({ size = 30 }: { size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: T.black,
        color: T.white,
        fontSize: size <= 28 ? 10 : 11,
        fontWeight: 700,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
      aria-hidden
    >
      BZ
    </div>
  );
}

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
  const [collapsed, setCollapsed] = useState(false);

  const sidebarWidth = collapsed
    ? SIDEBAR_WIDTH_COLLAPSED
    : SIDEBAR_WIDTH_EXPANDED;

  return (
    <aside
      style={{
        width: sidebarWidth,
        minWidth: sidebarWidth,
        background: T.sidebar,
        borderRight: `1px solid ${T.border}`,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        fontFamily: T.fontSans,
        color: T.black,
        transition: "width 0.2s ease, min-width 0.2s ease",
        overflow: "hidden",
      }}
    >
      {/* Top bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "flex-start",
          padding: collapsed ? "10px 0" : "14px 16px",
          borderBottom: `1px solid ${T.border}`,
          flexShrink: 0,
        }}
      >
        {!collapsed ? (
          <button
            type="button"
            onClick={onBack}
            aria-label="Back to research spaces"
            style={iconButtonBase}
          >
            <Icon.Back />
          </button>
        ) : null}
        {!collapsed ? (
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
        ) : null}
        <button
          type="button"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={() => setCollapsed((c) => !c)}
          style={iconButtonBase}
        >
          <Icon.Sidebar />
        </button>
      </div>

      {!collapsed ? (
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
      ) : null}

      {/* Tab nav — always visible; icon-only when collapsed */}
      <nav
        style={{
          flexShrink: 0,
          flex: collapsed ? 1 : undefined,
          paddingTop: collapsed ? 4 : 0,
        }}
      >
        {tabs.map(({ id, label, Icon: TabIcon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              title={label}
              aria-label={label}
              onClick={() => onTabChange(id)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: collapsed ? "center" : "flex-start",
                gap: collapsed ? 0 : 10,
                padding: collapsed ? "10px 0" : "9px 20px",
                border: "none",
                borderRadius: collapsed ? 8 : 0,
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
              {!collapsed ? label : null}
            </button>
          );
        })}
      </nav>

      {collapsed ? (
        <div
          style={{
            flexShrink: 0,
            padding: "12px 0",
            borderTop: `1px solid ${T.border}`,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <div
            title="Bruce Zhang"
            aria-label="Bruce Zhang"
            style={{ display: "flex" }}
          >
            <UserProfileAvatar />
          </div>
        </div>
      ) : null}

      {!collapsed ? (
      <>
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
            <UserProfileAvatar />
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
      </>
      ) : null}
    </aside>
  );
}
