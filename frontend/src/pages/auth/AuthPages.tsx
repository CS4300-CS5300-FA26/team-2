import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, apiPost } from "../../api/client";
import { useAuth } from "../../auth";
import type { User } from "../../auth";
import Alert from "../../components/Alert";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Field from "../../components/Field";

// Shared form plumbing: submit JSON, surface {"errors": {...}} from Django per field.
function useAuthForm(path: string, onDone: (user: User) => void) {
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [busy, setBusy] = useState(false);
  const { setUser } = useAuth();

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    const data = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    try {
      const { user } = await apiPost<{ user: User }>(path, data);
      setUser(user);
      onDone(user);
    } catch (err) {
      setErrors(err instanceof ApiError && Object.keys(err.fieldErrors).length ? err.fieldErrors : { __all__: [err instanceof ApiError && err.data?.detail ? err.data.detail : "Something went wrong. Try again."] });
    } finally {
      setBusy(false);
    }
  };
  const err = (name: string) => errors[name]?.join(" ");
  return { submit, busy, err, general: err("__all__") };
}

function Shell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="auth-wrap">
      <Card>
        <h1>{title}</h1>
        <p className="muted">{subtitle}</p>
        {children}
      </Card>
    </div>
  );
}

const safeNext = (n: string | null) => (n && n.startsWith("/") && !n.startsWith("//") ? n : "/feed");

export function LoginPage() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const { user } = useAuth();
  const { submit, busy, err, general } = useAuthForm("/api/auth/login", () => nav(safeNext(params.get("next")), { replace: true }));
  if (user) return <Navigate to={safeNext(params.get("next"))} replace />;
  return (
    <Shell title="Log in" subtitle="Welcome back to Pathfinder.">
      <form className="bare" onSubmit={submit}>
        {general && <Alert>{general}</Alert>}
        <Field label="Username" name="username" autoComplete="username" required autoFocus error={err("username")} />
        <Field label="Password" name="password" type="password" autoComplete="current-password" required error={err("password")} />
        <Button variant="primary" block type="submit" disabled={busy}>{busy ? "Logging in..." : "Log in"}</Button>
      </form>
      <p className="muted">No account? <Link to="/signup">Sign up</Link></p>
    </Shell>
  );
}

export function SignupPage() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { submit, busy, err, general } = useAuthForm("/api/auth/signup", () => nav("/signup/profile", { replace: true }));
  if (user) return <Navigate to="/feed" replace />;
  return (
    <Shell title="Create your account" subtitle="Step 1 of 3: choose a username and password.">
      <form className="bare" onSubmit={submit}>
        {general && <Alert>{general}</Alert>}
        <Field label="Username" name="username" autoComplete="username" required autoFocus error={err("username")} hint="Letters, digits and @/./+/-/_ only." />
        <Field label="Password" name="password1" type="password" autoComplete="new-password" required error={err("password1")} />
        <Field label="Confirm password" name="password2" type="password" autoComplete="new-password" required error={err("password2")} />
        <Button variant="primary" block type="submit" disabled={busy}>{busy ? "Creating..." : "Continue"}</Button>
      </form>
      <p className="muted">Already have an account? <Link to="/login">Log in</Link></p>
    </Shell>
  );
}

export function ProfilePage() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { submit, busy, err, general } = useAuthForm("/api/auth/signup/profile", (u) => nav(u.email_verified ? "/feed" : "/signup/verify", { replace: true }));
  return (
    <Shell title="Complete your profile" subtitle="Step 2 of 3: tell us a bit about yourself. This step is required.">
      <form className="bare" onSubmit={submit}>
        {general && <Alert>{general}</Alert>}
        <Field label="First name" name="first_name" autoComplete="given-name" required defaultValue={user?.first_name} error={err("first_name")} />
        <Field label="Last name" name="last_name" autoComplete="family-name" required defaultValue={user?.last_name} error={err("last_name")} />
        <Field label="Email" name="email" type="email" autoComplete="email" required defaultValue={user?.email} error={err("email")} />
        <Button variant="primary" block type="submit" disabled={busy}>{busy ? "Saving..." : "Finish"}</Button>
      </form>
    </Shell>
  );
}

export function VerifyPage() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { submit, busy, err, general } = useAuthForm("/api/auth/signup/verify", () => nav("/feed", { replace: true }));
  const [status, setStatus] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const resend = async () => {
    setStatus(null);
    try {
      const { detail } = await apiPost<{ detail: string }>("/api/auth/signup/resend");
      setStatus({ kind: "success", text: detail });
    } catch (e) {
      setStatus({ kind: "error", text: e instanceof ApiError && e.data?.detail ? e.data.detail : "Couldn't send a new code. Try again." });
    }
  };
  if (user?.email_verified) return <Navigate to="/feed" replace />;
  if (user && !user.profile_complete) return <Navigate to="/signup/profile" replace />;
  return (
    <Shell title="Verify your email" subtitle={`Step 3 of 3: we sent a 6-digit code to ${user?.email}. It works for 10 minutes.`}>
      <form className="bare" onSubmit={submit}>
        {general && <Alert>{general}</Alert>}
        {status && <Alert kind={status.kind}>{status.text}</Alert>}
        <Field label="Verification code" name="code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} required autoFocus error={err("code")} />
        <Button variant="primary" block type="submit" disabled={busy}>{busy ? "Checking..." : "Verify"}</Button>
      </form>
      <p className="muted">No email? <Button variant="ghost" size="sm" onClick={resend}>Resend code</Button></p>
    </Shell>
  );
}
