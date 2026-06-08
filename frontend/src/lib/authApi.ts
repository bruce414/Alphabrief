import { apiFetch } from "./api";

export type AuthResponse = {
  userId: string;
  email: string;
  displayName: string | null;
};

export function login(body: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function register(body: {
  email: string;
  password: string;
  displayName?: string;
}): Promise<AuthResponse> {
  return apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function logout(): Promise<void> {
  return apiFetch("/auth/logout", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
