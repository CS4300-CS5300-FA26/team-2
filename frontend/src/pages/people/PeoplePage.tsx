import { useState } from "react";
import type { FormEvent } from "react";
import { ApiError, apiGet } from "../../api/client";
import { useAuth } from "../../auth";
import Alert from "../../components/Alert";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Field from "../../components/Field";
import PageHeader from "../../components/PageHeader";

interface Person { username: string; first_name: string; last_name: string }

// US1.4: your username and real name are separate, and people who know your
// real name can find your account here.
export default function PeoplePage() {
  const { user } = useAuth();
  const [people, setPeople] = useState<Person[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const search = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const q = String(new FormData(e.currentTarget).get("q") ?? "").trim();
    setBusy(true);
    setError("");
    try {
      const r = await apiGet<{ people: Person[] }>(`/api/people/?q=${encodeURIComponent(q)}`);
      setPeople(r.people);
    } catch (err) {
      setError(err instanceof ApiError && err.data?.detail ? err.data.detail : "Search failed. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <PageHeader title="People" subtitle="Find someone by their real name or username." />
      {user && (
        <Card>
          <p className="muted">Your profile</p>
          <p><strong>{user.first_name} {user.last_name}</strong> <span className="muted">@{user.username}</span></p>
        </Card>
      )}
      <form onSubmit={search} role="search">
        <Field label="Name or username" name="q" type="search" minLength={2} required placeholder="e.g. Ada Lovelace" />
        <Button variant="primary" type="submit" disabled={busy}>{busy ? "Searching..." : "Search"}</Button>
      </form>
      {error && <Alert>{error}</Alert>}
      {people && (people.length ? (
        <ul aria-label="Search results">
          {people.map((p) => (
            <li key={p.username}><strong>{p.first_name} {p.last_name}</strong> <span className="muted">@{p.username}</span></li>
          ))}
        </ul>
      ) : <p className="muted" role="status">No one found.</p>)}
    </div>
  );
}
