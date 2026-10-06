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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    credentials: "same-origin",
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
