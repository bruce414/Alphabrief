import { Icon } from "@/components/workspace/icons";
import { T } from "@/styles/tokens";

export type FollowUpQuestionsBlockProps = {
  questions: string[];
  onSelect: (question: string) => void;
  disabled?: boolean;
};

export function FollowUpQuestionsBlock({
  questions,
  onSelect,
  disabled = false,
}: FollowUpQuestionsBlockProps) {
  if (!questions.length) return null;

  return (
    <div
      style={{
        marginTop: 16,
        paddingTop: 14,
        borderTop: `1px solid ${T.border}`,
      }}
    >
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          color: T.gray400,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          fontFamily: T.fontSans,
          marginBottom: 10,
        }}
      >
        Follow-up questions
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        {questions.map((q, i) => (
          <button
            key={`${i}-${q.slice(0, 48)}`}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(q)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              width: "100%",
              textAlign: "left",
              padding: "10px 12px",
              borderRadius: 10,
              border: `1px solid ${T.border}`,
              background: T.white,
              cursor: disabled ? "not-allowed" : "pointer",
              fontFamily: T.fontSans,
              fontSize: 13,
              lineHeight: 1.45,
              color: T.black,
              opacity: disabled ? 0.55 : 1,
              boxSizing: "border-box",
            }}
          >
            <span style={{ flex: 1, minWidth: 0 }}>{q}</span>
            <span
              aria-hidden
              style={{
                flexShrink: 0,
                display: "flex",
                alignItems: "center",
                color: T.gray500,
              }}
              title="Ask this"
            >
              <Icon.ReplyReturn width={16} height={16} />
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
