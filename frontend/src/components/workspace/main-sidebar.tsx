import { useState, type CSSProperties } from "react";

import { AlphaBriefLogo } from "@/components/workspace/logo";
import { Icon } from "@/components/workspace/icons";
import { useChats } from "@/hooks/useChats";
import { sortChatsByRecent } from "@/lib/chatSort";
import { useProjects } from "@/hooks/useProjects";
import { T } from "@/styles/tokens";

const SIDEBAR_WIDTH_EXPANDED = 280;
const SIDEBAR_WIDTH_COLLAPSED = 56;

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

export type MainSidebarProps = {
  currentView: "home" | "research" | "discover";
  onNavigate: (view: "home" | "research" | "discover") => void;
  activeChatId: string | null;
  onChatSelect: (chatId: string) => void;
  onNewChat: () => void;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
};

export function MainSidebar({
  currentView,
  onNavigate,
  activeChatId,
  onChatSelect,
  onNewChat,
  collapsed: collapsedProp,
  onCollapsedChange,
}: MainSidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const collapsed = collapsedProp ?? internalCollapsed;
  const setCollapsed = onCollapsedChange ?? setInternalCollapsed;
  const sidebarWidth = collapsed
    ? SIDEBAR_WIDTH_COLLAPSED
    : SIDEBAR_WIDTH_EXPANDED;
  const date = new Date();
  const dayName = date.toLocaleDateString("en-US", { weekday: "long" });
  const dayNum = date.getDate();
  const mon = date
    .toLocaleDateString("en-US", { month: "short" })
    .toUpperCase();
  const yyyy = date.getFullYear();
  const wn = Math.ceil(date.getDate() / 7);

  const { catchall, isLoading: projectsLoading } = useProjects();
  const catchallId = catchall?.id;
  const { chats, isLoading: chatsLoading } = useChats(catchallId);
  const quickChats =
    !projectsLoading && !chatsLoading ? sortChatsByRecent(chats) : [];

  const navItems: {
    key: "home" | "research" | "discover";
    label: string;
    icon: typeof Icon.Home;
    badge?: string;
  }[] = [
    { key: "home", label: "Home", icon: Icon.Home },
    { key: "research", label: "Research space", icon: Icon.ResearchSpace, badge: "4" },
    { key: "discover", label: "Discover", icon: Icon.Discover },
  ];

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
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed ? "12px 0" : "14px 16px 8px",
          flexShrink: 0,
        }}
      >
        {!collapsed ? <AlphaBriefLogo size={22} /> : null}
        <button
          type="button"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={() => setCollapsed(!collapsed)}
          style={iconButtonBase}
        >
          <Icon.Sidebar />
        </button>
      </div>

      {!collapsed ? (
      <>
      {/* Logo + date */}
      <div style={{ padding: "0 20px 12px" }}>
        <div style={{ marginTop: 0 }}>
          <div
            style={{
              fontSize: 12,
              color: T.gray400,
              fontWeight: 400,
            }}
          >
            {dayName}
          </div>
          <div
            style={{
              fontSize: 52,
              fontWeight: 800,
              color: T.black,
              letterSpacing: "-0.03em",
              lineHeight: 1,
              marginTop: 4,
            }}
          >
            {dayNum}
          </div>
          <div
            style={{
              fontSize: 11,
              color: T.gray400,
              letterSpacing: "0.05em",
              marginTop: 6,
            }}
          >
            {mon} · {yyyy} · {wn}
          </div>
        </div>
      </div>

      {/* New chat */}
      <div style={{ padding: "0 12px 12px" }}>
        <button
          type="button"
          onClick={onNewChat}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            padding: "10px 14px",
            background: T.black,
            color: T.white,
            border: "none",
            borderRadius: 10,
            cursor: "pointer",
            fontFamily: T.fontSans,
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Icon.Plus size={14} />
            New chat
          </span>
          <span
            style={{
              opacity: 0.5,
              fontSize: 11,
              padding: "3px 6px",
              borderRadius: 6,
              background: "rgba(255,255,255,0.15)",
            }}
          >
            ⌘N
          </span>
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: "0 12px 12px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 10px",
            borderRadius: 8,
            background: T.gray100,
            border: `1px solid ${T.border}`,
          }}
        >
          <Icon.Search style={{ flexShrink: 0, color: T.gray400 }} />
          <span
            style={{
              flex: 1,
              fontSize: 13,
              color: T.gray400,
            }}
          >
            Search...
          </span>
          <span
            style={{
              fontSize: 11,
              color: T.gray400,
              opacity: 0.9,
            }}
          >
            ⌘K
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ display: "flex", flexDirection: "column" }}>
        {navItems.map(({ key, label, icon: NavIcon, badge }) => {
          const active = currentView === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onNavigate(key)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 10,
                padding: "10px 16px",
                border: "none",
                background: active ? T.gray200 : "transparent",
                cursor: "pointer",
                fontFamily: T.fontSans,
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                color: T.black,
                textAlign: "left",
              }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <NavIcon
                  style={{
                    flexShrink: 0,
                    color: active ? T.black : T.gray400,
                  }}
                />
                {label}
              </span>
              {badge ? (
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: T.gray500,
                    minWidth: 20,
                    textAlign: "center",
                  }}
                >
                  {badge}
                </span>
              ) : null}
            </button>
          );
        })}
      </nav>

      <div
        style={{
          height: 1,
          background: T.border,
          margin: "12px 0",
        }}
      />

      {/* Quick chats */}
      <div
        style={{
          fontSize: 10,
          fontWeight: 600,
          color: T.gray400,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          padding: "0 16px 6px",
        }}
      >
        Quick Chats
      </div>

      <div
        style={{
          flex: 1,
          overflow: "auto",
          padding: "0 8px",
          minHeight: 0,
        }}
      >
        {quickChats.length > 0
          ? quickChats.map((chat) => {
              const selected = activeChatId === chat.id;
              return (
                <button
                  key={chat.id}
                  type="button"
                  onClick={() => onChatSelect(chat.id)}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 8,
                    padding: "8px 10px",
                    marginBottom: 4,
                    border: "none",
                    borderRadius: 8,
                    background: selected ? T.gray200 : "transparent",
                    cursor: "pointer",
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
                      {chat.title || "Untitled"}
                    </span>
                    <span
                      style={{
                        display: "block",
                        fontSize: 11,
                        color: T.gray400,
                        marginTop: 2,
                      }}
                    >
                      {formatRelativeTime(chat.lastTurnAt)}
                    </span>
                  </span>
                </button>
              );
            })
          : null}
      </div>

      </>
      ) : (
        <nav
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            paddingTop: 8,
            minHeight: 0,
          }}
        >
          {navItems.map(({ key, icon: NavIcon }) => {
            const active = currentView === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => onNavigate(key)}
                title={key}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "10px 0",
                  border: "none",
                  background: active ? T.gray200 : "transparent",
                  cursor: "pointer",
                }}
              >
                <NavIcon
                  style={{
                    flexShrink: 0,
                    color: active ? T.black : T.gray400,
                  }}
                />
              </button>
            );
          })}
        </nav>
      )}

      {/* User footer */}
      <div
        style={{
          padding: collapsed ? "12px 0" : "12px 16px",
          borderTop: `1px solid ${T.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "flex-start",
          gap: 10,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 30,
            height: 30,
            borderRadius: "50%",
            background: T.black,
            color: T.white,
            fontSize: 11,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          BZ
        </div>
        {!collapsed ? (
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: T.black,
            }}
          >
            Bruce Zhang
          </div>
          <div style={{ fontSize: 11, color: T.gray400 }}>Pro</div>
        </div>
        ) : null}
        {!collapsed ? (
          <button
            type="button"
            style={{
              border: "none",
              background: "transparent",
              padding: 6,
              cursor: "pointer",
              color: T.gray400,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            aria-label="Settings"
          >
            <Icon.Settings />
          </button>
        ) : null}
      </div>
    </aside>
  );
}
