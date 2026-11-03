// Resumes API helpers. XHR (not fetch) so uploads can report progress.
// ponytail: local copy of the CSRF/JSON handling in api/client.ts; swap to apiGet/apiPost once merged.
export class ApiError extends Error {
  status: number;
  errors: Record<string, string[]>;
  constructor(status: number, message: string, errors: Record<string, string[]> = {}) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

function csrf(): string {
  const m = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
  return m ? decodeURIComponent(m[1]) : "";
}

export function call<T>(
  method: "GET" | "POST",
  path: string,
  body?: FormData,
  onProgress?: (pct: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, path);
    xhr.withCredentials = true;
    xhr.setRequestHeader("Accept", "application/json");
    if (method === "POST") xhr.setRequestHeader("X-CSRFToken", csrf());
    if (onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
      };
    }
    xhr.onerror = () => reject(new ApiError(0, "Network error. Check your connection and try again."));
    xhr.onload = () => {
      let data: { detail?: string; errors?: Record<string, string[]> } | null = null;
      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        /* non-JSON error page */
      }
      if (xhr.status >= 200 && xhr.status < 300) return resolve(data as T);
      reject(new ApiError(xhr.status, data?.detail ?? `Request failed (${xhr.status})`, data?.errors));
    };
    xhr.send(body);
  });
}

export interface Resume {
  id: number;
  name: string;
  url: string;
  uploaded_at: string;
}
export interface Feedback {
  resume: Resume;
  feedback: string;
  suggestions: string[];
}

export const listResumes = () => call<{ results: Resume[] }>("GET", "/api/resumes/");
export const requestFeedback = (id: number) => call<Feedback>("POST", `/api/resumes/${id}/feedback/`);
export function uploadResume(file: File, onProgress: (pct: number) => void) {
  const fd = new FormData();
  fd.append("file", file);
  return call<Resume>("POST", "/api/resumes/", fd, onProgress);
}
