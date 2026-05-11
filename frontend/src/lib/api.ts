/**
 * Resolve API origin + `/api/v1` prefix.
 * - Uses `||` so empty-string env vars fall back ( `??` does not ).
 * - If `VITE_API_BASE_URL` is a bare origin like `http://localhost:8000`,
 *   append `/api/v1` (common misconfiguration in .env).
 */
function getApiBase(): string {
  let raw = import.meta.env.VITE_API_BASE_URL;
  if (raw === undefined || raw === null) {
    return "/api/v1";
  }
  let base = String(raw).trim();
  if (base === "") {
    return "/api/v1";
  }
  base = base.replace(/\/+$/, "");
  if (/^https?:\/\/[^/]+$/.test(base)) {
    base = `${base}/api/v1`;
  }
  return base;
}

const BASE = getApiBase();

export class ApiError extends Error {
  code: string;
  status: number;
  details?: unknown;

  constructor(code: string, message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = (body as { error?: { code?: string; message?: string; details?: unknown } }).error ?? {};
    throw new ApiError(
      err.code ?? "UNKNOWN",
      err.message ?? res.statusText,
      res.status,
      err.details,
    );
  }
  return res.json() as Promise<T>;
}
