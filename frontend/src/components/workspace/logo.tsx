import { T } from "../../styles/tokens";

const LOGO_SRC = "/alphabrief_offical_logo.png";

export function AlphaBriefLogo({
  size = 28,
  showText = true,
}: {
  size?: number;
  showText?: boolean;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <img
        src={LOGO_SRC}
        width={size}
        height={size}
        alt={showText ? "" : "AlphaBrief"}
        style={{ display: "block", objectFit: "contain" }}
      />
      {showText && (
        <span
          style={{
            fontFamily: T.fontSans,
            fontWeight: 600,
            fontSize: size * 0.64,
            color: T.black,
            letterSpacing: "-0.02em",
          }}
        >
          AlphaBrief
        </span>
      )}
    </div>
  );
}
