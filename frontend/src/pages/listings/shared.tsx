import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

// Sprint 3: created_at is when the note was written, like "2026-11-09T19:10:00+00:00"
export type Note = { id: number; text: string; created_at: string };
export type Listing = {
  id: number;
  title: string;
  company: string;
  // Sprint 3: details from imported JobDataLake jobs (empty strings for hand-added ones)
  location: string;
  remote_type: string;
  apply_url: string;
  saved: boolean;
  score: number | null;
  reasoning: string;
  notes?: Note[];
  // Sprint 3 (US4.5): only on the Saved Jobs page, like "applied"
  status?: string;
};

export function errorText(e: unknown): string {
  const msg = e instanceof Error ? e.message : "";
  return msg && !/^Request failed/.test(msg) ? msg : "Something went wrong. Please try again.";
}

// Redirects to /login on a 401 from any API call; returns true if it did.
export function useAuthRedirect() {
  const navigate = useNavigate();
  return (e: unknown) => {
    const err = e as { status?: number };
    if (err?.status === 401) {
      navigate(`/login?next=${encodeURIComponent(window.location.pathname)}`);
      return true;
    }
    return false;
  };
}

function tone(score: number) {
  return score < 50 ? "red" : score < 70 ? "orange" : score < 90 ? "yellow" : "green";
}

export function CredScore({ listing }: { listing: Listing }) {
  const { score, reasoning, id } = listing;
  if (score === null) {
    return (
      <span className="credscore credscore--unscored" role="img" aria-label="Credibility score unavailable">
        —
      </span>
    );
  }
  const badge = (
    <span className={`credscore credscore--${tone(score)}`} aria-hidden={reasoning ? true : undefined}>
      {score}
    </span>
  );
  if (!reasoning) {
    return (
      <span className={`credscore credscore--${tone(score)}`} role="img" aria-label={`Credibility score ${score} out of 100`}>
        {score}
      </span>
    );
  }
  return (
    <span className="credscore-tooltip" tabIndex={0} aria-label={`Credibility score ${score}`} aria-describedby={`reasons-${id}`}>
      {badge}
      <span className="credscore-reasons" id={`reasons-${id}`} role="tooltip">
        {reasoning}
      </span>
    </span>
  );
}

// Native <dialog>: focus trap, Esc to cancel and aria-modal come for free.
export function ConfirmDialog({
  open, message, confirmLabel, onConfirm, onCancel,
}: { open: boolean; message: string; confirmLabel: string; onConfirm: () => void; onCancel: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} className="confirm-dialog" aria-labelledby="confirm-msg" onCancel={(e) => { e.preventDefault(); onCancel(); }}>
      <p id="confirm-msg">{message}</p>
      <div className="confirm-actions">
        <button type="button" className="btn" onClick={onCancel} autoFocus>Cancel</button>
        <button type="button" className="btn listings-danger" onClick={onConfirm}>{confirmLabel}</button>
      </div>
    </dialog>
  );
}


// Sprint 3: turns the API's remote_type values into words people can read
const REMOTE_LABELS: Record<string, string> = {
  fully_remote: "Remote",
  hybrid: "Hybrid",
  on_site: "On-site",
};

// Sprint 3: shows a job's location, remote type, and an Apply link.
// Example: "Denver, CO · Hybrid  Apply"
// Listings added by hand in admin don't have these, so it shows nothing for them.
export function JobDetails({ listing }: { listing: Listing }) {
  // pull the three fields we need out of the listing
  const { location, remote_type, apply_url } = listing;

  // "hybrid" -> "Hybrid" (undefined if there's no remote type)
  const remote = REMOTE_LABELS[remote_type];

  // put location and remote type together with a dot between them,
  // skipping any that are empty
  const place = [location, remote].filter(Boolean).join(" · ");

  // nothing to show? then show nothing at all
  if (!place && !apply_url) {
    return null;
  }

  return (
    <p className="job-details">
      {place}
      {/* only show the Apply link if the job has one */}
      {apply_url && (
        <>
          {" "}
          {/* target="_blank" opens a new tab; rel="noopener noreferrer" keeps that tab
              from being able to control our page (a safety rule for outside links) */}
          <a href={apply_url} target="_blank" rel="noopener noreferrer">Apply</a>
        </>
      )}
    </p>
  );
}


// Sprint 3 (US4.5 / US4.6): the statuses a saved job can have.
// "value" is what the API uses, "label" is what people see.
export const STATUSES = [
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offer", label: "Offer" },
  { value: "rejected", label: "Rejected" },
];

// Sprint 3: turns "2026-11-09T19:10:00+00:00" into "Nov 9, 2026, 12:10 PM"
// in the viewer's own time zone.
export function formatDate(iso: string) {
  return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
