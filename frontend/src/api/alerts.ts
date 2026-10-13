export interface Alert {
  id: number;
  keywords: string;
  location: string;
  job_type: string;
  notify_method: "email" | "in_app";
  frequency: "instant" | "daily";
  digest_time: string;
  is_active: boolean;
  last_digest_sent_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  alert: number;
  listing: number;
  listing_title: string;
  listing_company: string;
  created_at: string;
  read: boolean;
}

export type AlertInput = Partial<
  Pick<Alert, "keywords" | "location" | "job_type" | "notify_method" | "frequency" | "digest_time" | "is_active">
>;

const SAFE_METHODS = ["GET", "HEAD", "OPTIONS", "TRACE"];
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

// The API lives on a different origin from this app (no shared gateway in
// this deploy), so document.cookie can't see its csrftoken cookie -- fetch
// the token from the API's own bootstrap endpoint instead, once, and reuse it.
let csrfTokenPromise: Promise<string> | null = null;
function getCsrfToken(): Promise<string> {
  csrfTokenPromise ??= fetch(`${API_BASE}/api/csrf/`, { credentials: "include" })
    .then((res) => res.json())
    .then((data: { csrfToken: string }) => data.csrfToken);
  return csrfTokenPromise;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method ?? "GET").toUpperCase();
  // DRF's SessionAuthentication rejects unsafe requests from logged-in users without this header.
  const csrfToken = SAFE_METHODS.includes(method) ? null : await getCsrfToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      ...init?.headers,
    },
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Request to ${path} failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const fetchAlerts = () => request<Alert[]>("/api/alerts/");

export const createAlert = (data: AlertInput) =>
  request<Alert>("/api/alerts/", { method: "POST", body: JSON.stringify(data) });

export const updateAlert = (id: number, data: AlertInput) =>
  request<Alert>(`/api/alerts/${id}/`, { method: "PATCH", body: JSON.stringify(data) });

export const deleteAlert = (id: number) =>
  request<void>(`/api/alerts/${id}/`, { method: "DELETE" });

export const fetchNotifications = () => request<Notification[]>("/api/notifications/");
