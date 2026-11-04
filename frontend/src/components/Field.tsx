import { useId } from "react";
import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: string };

/** Labelled input with accessible error/hint wiring. */
export default function Field({ label, error, hint, id, ...rest }: Props) {
  const auto = useId();
  const inputId = id ?? auto;
  const describedBy = [error && `${inputId}-err`, hint && `${inputId}-hint`].filter(Boolean).join(" ") || undefined;
  return (
    <div className="field">
      <label htmlFor={inputId}>{label}</label>
      <input id={inputId} aria-invalid={error ? true : undefined} aria-describedby={describedBy} {...rest} />
      {hint && <span id={`${inputId}-hint`} className="hint">{hint}</span>}
      {error && <span id={`${inputId}-err`} className="error">{error}</span>}
    </div>
  );
}
