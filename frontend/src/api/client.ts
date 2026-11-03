// Shared fetch wrapper. Exports: apiGet, apiPost, apiDelete, ApiError.
// Sends cookies, adds Django's X-CSRFToken on unsafe methods (fetching the cookie
// from GET /api/auth/csrf on first use), and throws ApiError on non-2xx.
const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(public status: number, public data: any) {
    super(`Request failed: ${status}`);
  }
  /** Field errors as { field: [msgs] } ("__all__" = non-field), from {"errors": {...}} bodies. */
  get fieldErrors(): Record<string, string[]> {
    return this.data?.errors ?? {};
  }
}

const cookie = (name: string) =>
  document.cookie.split("; ").find((r) => r.startsWith(`${name}=`))?.slice(name.length + 1);

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") {
    if (!cookie("csrftoken")) await fetch(`${BASE}/api/auth/csrf`, { credentials: "include" });
    headers["X-CSRFToken"] = decodeURIComponent(cookie("csrftoken") ?? "");
  }
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    credentials: "include",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = res.status === 204 ? undefined : await res.json().catch(() => undefined);
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export const apiGet = <T>(path: string) => request<T>("GET", path);
export const apiPost = <T>(path: string, body?: unknown) => request<T>("POST", path, body ?? {});
export const apiDelete = <T = void>(path: string) => request<T>("DELETE", path);
