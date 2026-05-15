import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { useSWRConfig } from "swr";

import { Icon } from "@/components/workspace/icons";
import {
  applyResearchDirection,
  getProjectCanvas,
  suggestResearchDirections,
} from "@/lib/workspaceApi";
import { T } from "@/styles/tokens";
import type { ResearchDirection } from "@/types/workspace";

type ModalState = "intro" | "describe" | "directions" | "applying";

export function onboardingDismissStorageKey(projectId: string): string {
  return `onboardingDismissed:${projectId}`;
}

export function readOnboardingDismissed(projectId: string): boolean {
  try {
    return localStorage.getItem(onboardingDismissStorageKey(projectId)) === "1";
  } catch {
    return false;
  }
}

export function writeOnboardingDismissed(projectId: string): void {
  try {
    localStorage.setItem(onboardingDismissStorageKey(projectId), "1");
  } catch {
    /* ignore quota / private mode */
  }
}

type OnboardingModalProps = {
  open: boolean;
  projectId: string;
  onDismiss: () => void;
  onFocusChat: () => void;
};

const panelStyle: CSSProperties = {
  width: "100%",
  maxWidth: 640,
  maxHeight: "min(720px, calc(100dvh - 48px))",
  background: T.white,
  borderRadius: 16,
  boxShadow: "0 16px 48px rgba(0,0,0,0.14)",
  fontFamily: T.fontSans,
  position: "relative",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  boxSizing: "border-box",
};

const panelScrollStyle: CSSProperties = {
  flex: 1,
  minHeight: 0,
  overflowY: "auto",
  overflowX: "hidden",
  padding: "28px 40px 32px 32px",
  WebkitOverflowScrolling: "touch",
  overscrollBehavior: "contain",
};

const titleStyle: CSSProperties = {
  fontSize: 20,
  fontWeight: 700,
  color: T.black,
  margin: "0 0 20px",
  lineHeight: 1.3,
};

const primaryButtonStyle: CSSProperties = {
  width: "100%",
  padding: "14px 18px",
  borderRadius: 10,
  border: `1px solid ${T.border}`,
  background: T.white,
  color: T.black,
  fontFamily: T.fontSans,
  fontSize: 15,
  fontWeight: 600,
  textAlign: "left",
  cursor: "pointer",
  transition: "background 0.15s ease, border-color 0.15s ease",
};

const chipStyle: CSSProperties = {
  display: "inline-block",
  fontSize: 11,
  fontWeight: 500,
  color: T.black,
  background: T.gray100,
  border: `1px solid ${T.border}`,
  borderRadius: 999,
  padding: "4px 10px",
  lineHeight: 1.2,
};

function Spinner({ label }: { label?: string }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 16,
        padding: "24px 0",
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          border: `2px solid ${T.gray200}`,
          borderTopColor: T.black,
          animation: "onboarding-spin 0.7s linear infinite",
        }}
      />
      {label ? (
        <p style={{ margin: 0, fontSize: 14, color: T.gray600 }}>{label}</p>
      ) : null}
    </div>
  );
}

function BackLink({ onClick, disabled }: { onClick: () => void; disabled?: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      style={{
        marginTop: 16,
        padding: 0,
        border: "none",
        background: "transparent",
        fontFamily: T.fontSans,
        fontSize: 13,
        fontWeight: 500,
        color: T.gray600,
        cursor: disabled ? "not-allowed" : "pointer",
        textDecoration: "underline",
        textUnderlineOffset: 3,
      }}
    >
      Back
    </button>
  );
}

function scopeChips(direction: ResearchDirection): string[] {
  return [...direction.includedTopics, ...direction.targetEntities].slice(0, 5);
}

export function OnboardingModal({
  open,
  projectId,
  onDismiss,
  onFocusChat,
}: OnboardingModalProps) {
  const { mutate: mutateGlobal } = useSWRConfig();
  const [state, setState] = useState<ModalState>("intro");
  const [description, setDescription] = useState("");
  const [directions, setDirections] = useState<ResearchDirection[]>([]);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestError, setSuggestError] = useState<string | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  const resetFlow = useCallback(() => {
    setState("intro");
    setDescription("");
    setDirections([]);
    setSuggesting(false);
    setSuggestError(null);
    setApplyError(null);
  }, []);

  useEffect(() => {
    if (!open) resetFlow();
  }, [open, resetFlow]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && state !== "applying") onDismiss();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onDismiss, state]);

  const handleSuggest = async () => {
    const text = description.trim();
    if (text.length < 10 || suggesting) return;
    setSuggesting(true);
    setSuggestError(null);
    try {
      const res = await suggestResearchDirections(projectId, text);
      setDirections(res.directions);
      setState("directions");
    } catch {
      setSuggestError("Could not suggest directions. Please try again.");
    } finally {
      setSuggesting(false);
    }
  };

  const handleApply = async (direction: ResearchDirection) => {
    setState("applying");
    setApplyError(null);
    try {
      const overview = await applyResearchDirection(projectId, direction);
      const canvas = await getProjectCanvas(projectId);
      await Promise.all([
        mutateGlobal(["overview", projectId], overview, { revalidate: false }),
        mutateGlobal(["canvasElements", canvas.id]),
        mutateGlobal(["canvasConnections", canvas.id]),
        mutateGlobal(["projects"]),
      ]);
      writeOnboardingDismissed(projectId);
      onDismiss();
    } catch {
      setApplyError("Could not set up your research space. Please try again.");
      setState("directions");
    }
  };

  if (!open) return null;

  const describeLen = description.trim().length;
  const canSuggest = describeLen >= 10 && describeLen <= 500 && !suggesting;

  return (
    <>
      <style>{`
        @keyframes onboarding-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    <div
      role="presentation"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 2000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        boxSizing: "border-box",
        overflowY: "auto",
        background: "rgba(26, 26, 26, 0.35)",
        backdropFilter: "blur(4px)",
      }}
      onClick={state === "applying" ? undefined : onDismiss}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-modal-title"
        onClick={(e) => e.stopPropagation()}
        style={panelStyle}
      >
        {state !== "applying" ? (
          <button
            type="button"
            aria-label="Close"
            onClick={onDismiss}
            style={{
              position: "absolute",
              top: 16,
              right: 16,
              zIndex: 2,
              width: 32,
              height: 32,
              border: "none",
              borderRadius: 8,
              background: T.white,
              color: T.gray500,
              boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
              cursor: "pointer",
              fontSize: 22,
              lineHeight: 1,
              fontFamily: T.fontSans,
            }}
          >
            ×
          </button>
        ) : null}

        <div style={panelScrollStyle}>
        {state === "intro" ? (
          <>
            <h2 id="onboarding-modal-title" style={titleStyle}>
              Where do you want to start?
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <button
                type="button"
                style={primaryButtonStyle}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = T.gray100;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = T.white;
                }}
                onClick={() => {
                  writeOnboardingDismissed(projectId);
                  onDismiss();
                  onFocusChat();
                }}
              >
                I have a specific question →
              </button>
              <button
                type="button"
                style={primaryButtonStyle}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = T.gray100;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = T.white;
                }}
                onClick={() => setState("describe")}
              >
                Help me find a direction →
              </button>
            </div>
          </>
        ) : null}

        {state === "describe" ? (
          <>
            <h2 id="onboarding-modal-title" style={titleStyle}>
              Briefly describe what you want to research
            </h2>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value.slice(0, 500))}
              placeholder="AI infrastructure spending in 2026 — chip demand, hyperscaler capex, valuation implications"
              rows={4}
              autoFocus
              style={{
                width: "100%",
                padding: "12px 14px",
                borderRadius: 10,
                border: `1px solid ${T.border}`,
                fontFamily: T.fontSans,
                fontSize: 14,
                color: T.black,
                resize: "vertical",
                boxSizing: "border-box",
                minHeight: 100,
              }}
            />
            <p style={{ margin: "8px 0 0", fontSize: 12, color: T.gray500 }}>
              {describeLen}/500 characters
              {describeLen > 0 && describeLen < 10 ? " · at least 10 to continue" : ""}
            </p>
            {suggestError ? (
              <p style={{ margin: "12px 0 0", fontSize: 13, color: T.red500 }}>{suggestError}</p>
            ) : null}
            <button
              type="button"
              disabled={!canSuggest}
              onClick={() => void handleSuggest()}
              style={{
                marginTop: 20,
                width: "100%",
                padding: "12px 16px",
                borderRadius: 10,
                border: "none",
                background: canSuggest ? T.black : T.gray300,
                color: T.white,
                fontFamily: T.fontSans,
                fontSize: 14,
                fontWeight: 600,
                cursor: canSuggest ? "pointer" : "not-allowed",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
            >
              {suggesting ? (
                <>
                  <span
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: "50%",
                      border: "2px solid rgba(255,255,255,0.35)",
                      borderTopColor: T.white,
                      animation: "onboarding-spin 0.7s linear infinite",
                      flexShrink: 0,
                    }}
                  />
                  Suggesting…
                </>
              ) : (
                "Suggest directions"
              )}
            </button>
            <BackLink onClick={() => setState("intro")} disabled={suggesting} />
          </>
        ) : null}

        {state === "directions" ? (
          <>
            <h2 id="onboarding-modal-title" style={titleStyle}>
              Pick a starting direction
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {directions.map((direction) => (
                <div
                  key={direction.key}
                  style={{
                    border: `1px solid ${T.border}`,
                    borderRadius: 12,
                    padding: "16px 18px",
                    background: T.white,
                  }}
                >
                  <h3
                    style={{
                      margin: "0 0 8px",
                      fontSize: 16,
                      fontWeight: 700,
                      color: T.black,
                    }}
                  >
                    {direction.title}
                  </h3>
                  <p
                    style={{
                      margin: "0 0 12px",
                      fontSize: 14,
                      lineHeight: 1.5,
                      color: T.gray600,
                    }}
                  >
                    {direction.summary}
                  </p>
                  {scopeChips(direction).length > 0 ? (
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 6,
                        marginBottom: 12,
                      }}
                    >
                      {scopeChips(direction).map((chip) => (
                        <span key={chip} style={chipStyle}>
                          {chip}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <ul
                    style={{
                      margin: "0 0 14px",
                      paddingLeft: 18,
                      fontSize: 13,
                      color: T.gray600,
                      lineHeight: 1.45,
                    }}
                  >
                    {direction.starterElements.map((el) => (
                      <li key={el.title} style={{ marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, color: T.black }}>{el.title}</span>
                        {" — "}
                        {el.body.length > 120 ? `${el.body.slice(0, 117)}…` : el.body}
                      </li>
                    ))}
                  </ul>
                  <button
                    type="button"
                    onClick={() => void handleApply(direction)}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "8px 14px",
                      borderRadius: 8,
                      border: "none",
                      background: T.black,
                      color: T.white,
                      fontFamily: T.fontSans,
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Start with this
                    <Icon.ArrowUpRight width={14} height={14} />
                  </button>
                </div>
              ))}
            </div>
            {applyError ? (
              <p style={{ margin: "12px 0 0", fontSize: 13, color: T.red500 }}>{applyError}</p>
            ) : null}
            <BackLink onClick={() => setState("describe")} />
          </>
        ) : null}

        {state === "applying" ? (
          <>
            <h2 id="onboarding-modal-title" style={{ ...titleStyle, textAlign: "center" }}>
              Setting up your research space…
            </h2>
            <Spinner />
          </>
        ) : null}
        </div>
      </div>
    </div>
    </>
  );
}
