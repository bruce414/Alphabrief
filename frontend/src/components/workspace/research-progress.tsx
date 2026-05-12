import { useMemo, useState } from "react";

import { Icon } from "@/components/workspace/icons";
import { T } from "@/styles/tokens";
import type { ResearchEvent } from "@/types/workspace";

type Props = {
  events: ResearchEvent[];
  /** Whether the turn is still running. Used to auto-expand. */
  loading?: boolean;
  /** Optional explicit hostname/title for the chat (currently unused). */
  className?: string;
};

function hostnameOf(url: string | null | undefined): string {
  if (!url) return "";
  try {
    return new URL(url).hostname.replace(/^www\./i, "");
  } catch {
    return url.replace(/^https?:\/\//i, "").split("/")[0] ?? "";
  }
}

function summarize(events: ResearchEvent[]): string {
  const searches = events.filter((e) => e.type === "search").length;
  const reads = events.filter((e) => e.type === "read").length;
  if (searches === 0 && reads === 0) return "Thinking";
  const parts: string[] = [];
  if (searches > 0)
    parts.push(`${searches} search${searches === 1 ? "" : "es"}`);
  if (reads > 0)
    parts.push(`${reads} source${reads === 1 ? "" : "s"}`);
  return `Researched ${parts.join(" · ")}`;
}

export function ResearchProgress({ events, loading = false }: Props) {
  const [expanded, setExpanded] = useState<boolean | null>(null);

  // Default: expanded while loading, collapsed when complete. User can override.
  const isOpen = expanded === null ? loading : expanded;

  const summary = useMemo(() => summarize(events), [events]);

  if (!events || events.length === 0) {
    if (!loading) return null;
    return (
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 10px",
          background: T.gray100,
          border: `1px solid ${T.border}`,
          borderRadius: 8,
          color: T.gray500,
          fontFamily: T.fontSans,
          fontSize: 11.5,
          marginBottom: 10,
        }}
      >
        <span
          style={{
            width: 5,
            height: 5,
            borderRadius: "50%",
            background: T.gray400,
            animation: "pulse 1.2s infinite",
            display: "inline-block",
          }}
        />
        Thinking…
      </div>
    );
  }

  return (
    <div
      style={{
        background: T.gray100,
        border: `1px solid ${T.border}`,
        borderRadius: 10,
        marginBottom: 10,
        overflow: "hidden",
        fontFamily: T.fontSans,
      }}
    >
      <button
        type="button"
        onClick={() => setExpanded(!isOpen)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 12px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: T.gray600,
          fontFamily: T.fontSans,
          fontSize: 11.5,
          fontWeight: 500,
          textAlign: "left",
        }}
      >
        {loading ? (
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: T.gray500,
              animation: "pulse 1.2s infinite",
              display: "inline-block",
              flexShrink: 0,
            }}
          />
        ) : (
          <Icon.Search width={12} height={12} style={{ flexShrink: 0 }} />
        )}
        <span style={{ flex: 1, minWidth: 0 }}>{summary}</span>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "transform 120ms ease",
            transform: isOpen ? "rotate(0deg)" : "rotate(-90deg)",
            color: T.gray400,
            flexShrink: 0,
          }}
        >
          <Icon.ChevronDown width={12} height={12} />
        </span>
      </button>

      {isOpen ? (
        <div
          style={{
            borderTop: `1px solid ${T.border}`,
            padding: "8px 12px 10px",
            background: T.white,
          }}
        >
          <ul
            style={{
              margin: 0,
              padding: 0,
              listStyle: "none",
              display: "flex",
              flexDirection: "column",
              gap: 6,
            }}
          >
            {events.map((event, i) => (
              <li
                key={`${event.type}-${i}`}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 8,
                  fontSize: 11.5,
                  color: T.gray600,
                  lineHeight: 1.5,
                }}
              >
                <span
                  style={{
                    color: T.gray400,
                    flexShrink: 0,
                    marginTop: 2,
                    display: "inline-flex",
                  }}
                >
                  {event.type === "search" ? (
                    <Icon.Search width={12} height={12} />
                  ) : event.type === "read" ? (
                    <Icon.Globe width={12} height={12} />
                  ) : (
                    <span
                      style={{
                        width: 5,
                        height: 5,
                        borderRadius: "50%",
                        background: T.gray400,
                        display: "inline-block",
                        marginTop: 4,
                      }}
                    />
                  )}
                </span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  {event.type === "search" ? (
                    <>
                      <span style={{ color: T.gray500 }}>
                        {event.status === "running" ? "Searching" : "Searched"}
                      </span>{" "}
                      <span style={{ color: T.black }}>
                        {event.query
                          ? `"${event.query}"`
                          : "the web"}
                      </span>
                    </>
                  ) : event.type === "read" ? (
                    <>
                      <span style={{ color: T.gray500 }}>Read</span>{" "}
                      {event.url ? (
                        <a
                          href={event.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            color: T.black,
                            textDecoration: "underline",
                            textUnderlineOffset: 2,
                          }}
                          title={event.url}
                        >
                          {event.title?.trim() ||
                            event.publisher ||
                            hostnameOf(event.url)}
                        </a>
                      ) : (
                        <span style={{ color: T.black }}>
                          {event.title ?? "a source"}
                        </span>
                      )}
                    </>
                  ) : event.type === "thinking" ? (
                    <span style={{ color: T.gray600 }}>
                      {event.text ?? "Thinking…"}
                    </span>
                  ) : (
                    <span style={{ color: T.gray600 }}>
                      {event.text ?? ""}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
