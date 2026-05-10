/** Raster crops from `alphabrief_offical_logo.png`: icon mark only + wordmark only */
const MARK_SRC = "/alphabrief_logo_mark.png";
const WORDMARK_SRC = "/alphabrief_logo_wordmark.png";

/** Wordmark crop height / icon crop height in source asset (aligns cap height to sidebar logo) */
const WORDMARK_HEIGHT_RATIO = 213 / 325;

export function AlphaBriefLogo({
  size = 28,
  showText = true,
}: {
  size?: number;
  showText?: boolean;
}) {
  const wordH = size * WORDMARK_HEIGHT_RATIO;

  return (
    <div
      role="img"
      aria-label="AlphaBrief"
      style={{ display: "flex", alignItems: "center", gap: 8 }}
    >
      <img
        src={MARK_SRC}
        height={size}
        alt=""
        style={{
          display: "block",
          height: size,
          width: "auto",
          objectFit: "contain",
        }}
      />
      {showText ? (
        <img
          src={WORDMARK_SRC}
          alt=""
          style={{
            display: "block",
            height: wordH,
            width: "auto",
            objectFit: "contain",
          }}
        />
      ) : null}
    </div>
  );
}
