import { T } from "@/styles/tokens";

export type SpaceLoadingProps = {
  projectTitle: string;
};

export function SpaceLoading({ projectTitle }: SpaceLoadingProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100vh",
        background: T.bg,
        fontFamily: T.fontSans,
        gap: 0,
      }}
    >
      <style>{`
        @keyframes space-loading-dash {
          from { stroke-dashoffset: 40; }
          to { stroke-dashoffset: -40; }
        }
      `}</style>
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: "50%",
          background: T.gray200,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 20,
        }}
      >
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden
        >
          <circle
            cx="12"
            cy="12"
            r="10"
            stroke={T.black}
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray="40"
            fill="none"
            style={{
              animation: "space-loading-dash 1.1s linear infinite",
            }}
          />
        </svg>
      </div>
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: T.gray400,
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          marginBottom: 10,
        }}
      >
        Opening space
      </div>
      <h2
        style={{
          fontFamily: T.fontSans,
          fontSize: 36,
          fontWeight: 800,
          color: T.black,
          letterSpacing: "-0.03em",
          margin: 0,
          lineHeight: 1.1,
          textAlign: "center",
          padding: "0 24px",
        }}
      >
        {projectTitle}
      </h2>
      <p
        style={{
          marginTop: 12,
          fontSize: 13,
          color: T.gray400,
          textAlign: "center",
          padding: "0 24px",
        }}
      >
        Loading threads, sources, memory, and canvas state...
      </p>
    </div>
  );
}
