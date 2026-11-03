import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiDelete, apiGet, apiPost } from "../../api/client";
import { ConfirmDialog, Listing, Note, errorText, useAuthRedirect } from "./shared";
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
  const authRedirect = useAuthRedirect();
  const fail = (e: unknown) => { if (!authRedirect(e)) setError(errorText(e)); };

  useEffect(() => {
    apiGet<{ listings: Listing[] }>("/api/listings/saved/")
      .then((d) => setListings(d.listings))
      .catch(fail);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      {error && <p role="alert" className="listings-error">{error}</p>}
      {listings === null && !error && <p role="status">Loading saved jobs…</p>}
      {listings?.length === 0 && <p>You haven't saved any jobs yet.</p>}
      <ul className="listings-list">
        {listings?.map((l) => (
          <li key={l.id} className="card listing saved-listing">
            <div className="saved-info">
              <h3>{l.title}</h3>
              <p>{l.company}</p>
              {!!l.notes?.length && (
                <ul className="notes">
                  {l.notes.map((n) => (
                    <li key={n.id} className="note">
                      <span>{n.text}</span>
                      <button type="button" className="delete-note-button" aria-label="Delete note" onClick={() => deleteNote(l, n)}>
                        &times;
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="actions">
              <NoteForm onAdd={(t) => addNote(l, t)} />
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
