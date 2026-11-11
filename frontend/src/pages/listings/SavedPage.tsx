import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiDelete, apiGet, apiPost } from "../../api/client";
import { ConfirmDialog, Listing, Note, errorText, useAuthRedirect, JobDetails, STATUSES, formatDate } from "./shared";
import "./listings.css";

function NoteForm({ onAdd }: { onAdd: (text: string) => Promise<void> }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      await onAdd(text);
      setText("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="note-form" onSubmit={submit}>
      <textarea
        rows={2}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Why did you save this job?"
        aria-label="New note"
      />
      <button type="submit" className="btn" disabled={busy || !text.trim()}>Add note</button>
    </form>
  );
}

export default function SavedPage() {
  const [listings, setListings] = useState<Listing[] | null>(null);
  const [error, setError] = useState("");
  const [confirming, setConfirming] = useState<Listing | null>(null);
  // Sprint 3 (US4.6): which status the "Show" filter is set to ("" = all)
  const [filter, setFilter] = useState("");
  const authRedirect = useAuthRedirect();
  const fail = (e: unknown) => { if (!authRedirect(e)) setError(errorText(e)); };

  // load my saved jobs, and load them again whenever the filter changes.
  // Sprint 3 (US4.6): with a filter, ask the API for only that status.
  useEffect(() => {
    const url = filter ? `/api/listings/saved/?status=${filter}` : "/api/listings/saved/";
    apiGet<{ listings: Listing[] }>(url)
      .then((d) => setListings(d.listings))
      .catch(fail);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const patchNotes = (id: number, fn: (n: Note[]) => Note[]) =>
    setListings((ls) => ls && ls.map((l) => (l.id === id ? { ...l, notes: fn(l.notes ?? []) } : l)));

  async function addNote(l: Listing, text: string) {
    setError("");
    try {
      const note = await apiPost<Note>(`/api/listings/${l.id}/notes/`, { note: text });
      patchNotes(l.id, (n) => [...n, note]);
    } catch (e) {
      fail(e);
      throw e; // keep the typed text in the box
    }
  }

  async function deleteNote(l: Listing, note: Note) {
    setError("");
    patchNotes(l.id, (n) => n.filter((x) => x.id !== note.id));
    try {
      await apiDelete(`/api/listings/notes/${note.id}/`);
    } catch (e) {
      patchNotes(l.id, (n) => [...n, note].sort((a, b) => a.id - b.id));
      fail(e);
    }
  }

  // Sprint 3 (US4.5): runs when a status is picked from a job's dropdown
  async function changeStatus(l: Listing, status: string) {
    // clicking the status it already has does nothing
    if ((l.status ?? "saved") === status) return;
    setError("");
    const before = listings;
    // show the new status right away
    setListings((ls) => ls && ls.map((x) => (x.id === l.id ? { ...x, status } : x)));
    try {
      await apiPost(`/api/listings/${l.id}/status/`, { status });
      // if a filter is on and this job no longer matches it, take it off the list
      if (filter && status !== filter) {
        setListings((ls) => ls && ls.filter((x) => x.id !== l.id));
      }
    } catch (e) {
      setListings(before); // it didn't save, so put the old status back
      fail(e);
    }
  }

  // US4.3: only runs after the user confirms in the dialog
  async function removeJob(l: Listing) {
    setConfirming(null);
    setError("");
    const before = listings;
    setListings((ls) => ls && ls.filter((x) => x.id !== l.id));
    try {
      await apiPost(`/api/listings/${l.id}/remove/`);
    } catch (e) {
      setListings(before);
      fail(e);
    }
  }

  return (
    <div className="listings-page">
      <header className="listings-header">
        <h1>Saved Jobs</h1>
        <Link to="/feed">Back to job feed</Link>
      </header>
      {/* Sprint 3 (US4.6): only show saved jobs with this status */}
      <label className="status-filter">
        Show:{" "}
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All</option>
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </label>
      {error && <p role="alert" className="listings-error">{error}</p>}
      {listings === null && !error && <p role="status">Loading saved jobs…</p>}
      {listings?.length === 0 && (
        <p>{filter ? "No saved jobs with this status." : "You haven't saved any jobs yet."}</p>
      )}
      <ul className="listings-list">
        {listings?.map((l) => (
          <li key={l.id} className="card listing saved-listing">
            <div className="saved-info">
              <h3>{l.title}</h3>
              <p>{l.company}</p>
              <JobDetails listing={l} />
              {!!l.notes?.length && (
                <ul className="notes">
                  {l.notes.map((n) => (
                    <li key={n.id} className="note">
                      <span>{n.text}</span>
                      {/* Sprint 3: when the note was written */}
                      <time className="note-date" dateTime={n.created_at}>{formatDate(n.created_at)}</time>
                      <button type="button" className="delete-note-button" aria-label="Delete note" onClick={() => deleteNote(l, n)}>
                        &times;
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="actions">
              <div className="note-column">
                {/* Sprint 3 (US4.5): a bar of the five statuses. The current one is highlighted.
                    aria-pressed tells screen readers which button is the current status. */}
                <div className="status-bar" role="group" aria-label="Application status">
                  {STATUSES.map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      className={`status-option status-option--${s.value}`}
                      aria-pressed={(l.status ?? "saved") === s.value}
                      onClick={() => changeStatus(l, s.value)}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
                <NoteForm onAdd={(t) => addNote(l, t)} />
              </div>
              <button type="button" className="btn listings-danger" onClick={() => setConfirming(l)}>
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>
      <ConfirmDialog
        open={confirming !== null}
        message="Remove this job and its notes?"
        confirmLabel="Remove"
        onCancel={() => setConfirming(null)}
        onConfirm={() => confirming && removeJob(confirming)}
      />
    </div>
  );
}
