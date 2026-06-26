/**
 * Auth utility helpers for the client-side.
 * Reads/writes the JWT from localStorage and decodes basic info.
 */

const TOKEN_KEY = "token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) return false;
  try {
    const payload = decodeToken(token);
    if (!payload?.exp) return false;
    // exp is in seconds; Date.now() is in ms
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface TokenPayload {
  sub: string;       // doctor ID (as string)
  exp: number;       // expiry unix timestamp
  email?: string;    // optional if backend embeds it
}

export function decodeToken(token: string): TokenPayload | null {
  try {
    const base64 = token.split(".")[1];
    const json = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json) as TokenPayload;
  } catch {
    return null;
  }
}

export function getDoctorId(): string | null {
  const token = getToken();
  if (!token) return null;
  return decodeToken(token)?.sub ?? null;
}
