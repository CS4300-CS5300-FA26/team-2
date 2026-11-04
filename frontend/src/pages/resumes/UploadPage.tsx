import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "./resumes.css";
import {ApiError, deleteResume, listResumes, replaceResume, uploadResume, type Resume,} from "./http";

const ALLOWED = [".pdf", ".doc", ".docx"];
const MAX = 5 * 1024 * 1024;

// Same rules as backend ResumeUploadForm; the server stays the source of truth.
function validate(f: File): string | null {
  const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
  if (!ALLOWED.includes(ext)) return "Please upload a PDF, DOC, or DOCX resume file.";
  if (f.size > MAX) return "Please upload a file smaller than 5 MB.";
  return null;
}

const toLogin = () =>
  window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname)}`);

export default function UploadPage() {
  const [resumes, setResumes] = useState<Resume[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [drag, setDrag] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [workingResumeId, setWorkingResumeId] = useState<number | null>(null);
  const input = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    listResumes()
      .then((r) => setResumes(r.results))
      .catch((e: ApiError) => (e.status === 401 ? toLogin() : setError(e.message)));
  }, []);
  useEffect(load, [load]);

  async function send(f: File | undefined) {
    if (!f) return;
    setDone(null);
    const bad = validate(f);
    if (bad) return setError(bad);
    setError(null);
    setProgress(0);
    try {
      await uploadResume(f, setProgress);
      setDone(`Uploaded ${f.name}`);
      load();
    } catch (e) {
      const err = e as ApiError;
      if (err.status === 401) return toLogin();
      setError(err.errors?.file?.join(" ") ?? err.message);
    } finally {
      setProgress(null);
      if (input.current) input.current.value = "";
    }
  }
  async function replace(id: number, file: File | undefined) {
    if (!file) return;

    setDone(null);

    const validationError = validate(file);

    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setWorkingResumeId(id);

    try {
      await replaceResume(id, file);
      setDone(`Replaced resume with ${file.name}`);
      load();
    } catch (error) {
      const apiError = error as ApiError;

      if (apiError.status === 401) {
        toLogin();
        return;
      }

      setError(
        apiError.errors?.file?.join(" ") ??
          apiError.message,
      );
    } finally {
      setWorkingResumeId(null);
    }
  }

  async function remove(resume: Resume) {
    const confirmed = window.confirm(
      `Delete ${resume.name}? This cannot be undone.`,
    );

    if (!confirmed) return;

    setDone(null);
    setError(null);
    setWorkingResumeId(resume.id);

    try {
      await deleteResume(resume.id);
      setDone(`Deleted ${resume.name}`);
      load();
    } catch (error) {
      const apiError = error as ApiError;

      if (apiError.status === 401) {
        toLogin();
        return;
      }

      setError(apiError.message);
    } finally {
      setWorkingResumeId(null);
    }
  }
  const busy = progress !== null;
  return (
    <div className="resumes-page">
      <section className="card">
        <h1>Upload your resume</h1>
        <p className="muted">PDF, DOC, or DOCX, up to 5 MB.</p>

        <div
          className={`dropzone${drag ? " drag" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            if (!busy) send(e.dataTransfer.files[0]);
          }}
        >
          <p>Drag and drop a file here, or</p>
          <label className="btn" htmlFor="resume-file" aria-disabled={busy}>
            Select a resume
          </label>
          <input
            id="resume-file"
            ref={input}
            className="sr-only"
            type="file"
            accept=".pdf,.doc,.docx"
            disabled={busy}
            onChange={(e) => send(e.target.files?.[0])}
          />
        </div>

        {busy && (
          <progress value={progress} max={100} aria-label="Upload progress">
            {progress}%
          </progress>
        )}
        <div aria-live="polite">
          {error && (
            <p role="alert" className="resumes-error">
              {error}
            </p>
          )}
          {done && <p className="resumes-ok">{done}</p>}
        </div>
      </section>

      <section className="card">
        <h2>Your uploaded resumes</h2>
        {resumes === null ? (
          <div className="skeleton" aria-busy="true" aria-label="Loading resumes" style={{ height: 64 }} />
        ) : resumes.length === 0 ? (
          <p className="muted">You have not uploaded a resume yet.</p>
        ) : (
          <>
            <ul className="resume-list">
              {resumes.map((r) => (
                <li key={r.id}>
                  <div>
                    <a href={r.url} target="_blank" rel="noopener noreferrer">
                      {r.name}
                    </a>
                    <span className="muted">Uploaded {new Date(r.uploaded_at).toLocaleString()}</span>
                  </div>
                  <div className="resume-actions">
                      <Link
                        className="btn"
                        to={`/resumes/${r.id}/feedback`}
                        aria-disabled={workingResumeId === r.id}
                      >
                        Get AI feedback
                      </Link>

                      <label
                        className="btn"
                        htmlFor={`replace-resume-${r.id}`}
                        aria-disabled={workingResumeId === r.id}
                      >
                        Replace
                      </label>

                      <input
                        id={`replace-resume-${r.id}`}
                        className="sr-only"
                        type="file"
                        accept=".pdf,.doc,.docx"
                        disabled={workingResumeId === r.id}
                        onChange={(event) => {
                          replace(r.id, event.target.files?.[0]);
                          event.target.value = "";
                        }}
                      />

                      <button
                        type="button"
                        className="btn btn-danger"
                        disabled={workingResumeId === r.id}
                        onClick={() => remove(r)}
                      >
                        {workingResumeId === r.id ? "Working..." : "Delete"}
                      </button>
                    </div>
                </li>
              ))}
            </ul>
            <p className="muted small">Requesting feedback sends the selected resume to the AI service.</p>
          </>
        )}
      </section>
    </div>
  );
}
