import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

export type Note = { id: number; text: string };
export type Listing = {
  id: number;
  title: string;
  company: string;
  saved: boolean;
  score: number | null;
  reasoning: string;
  notes?: Note[];
};

export function errorText(e: unknown): string {
  const msg = e instanceof Error ? e.message : "";
  return msg && !/^\d+$/.test(msg) ? msg : "Something went wrong. Please try again.";
}

// Redirects to /login on a 401 from any API call; returns true if it did.
export function useAuthRedirect() {
  const navigate = useNavigate();
  return (e: unknown) => {
    const err = e as { status?: number };
    if (err?.status === 401) {
      navigate("/login");
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
