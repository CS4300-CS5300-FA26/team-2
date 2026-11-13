import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost } from "../../api/client";
import { CredScore, Listing, errorText, useAuthRedirect, JobDetails } from "./shared";
import FilterMenu, { FeedFilters } from "./FilterMenu"; // In an effort to not touch other's work as much as possible
import "./listings.css";

export default function FeedPage() {
  const [listings, setListings] = useState<Listing[] | null>(null);
  const [error, setError] = useState("");
  // Initialize filters
  const [filters, setFilters] = useState<FeedFilters | null>(null);
  const authRedirect = useAuthRedirect();

  useEffect(() => {
    
    const query = filters
      ? "?" + new URLSearchParams({
          sort_by: filters.sortBy,
          min_score: String(filters.minScore),
          max_score: String(filters.maxScore),
        }).toString()
      : "";
    setError("");
    apiGet<{ listings: Listing[] }>(`/api/listings/feed/${query}`)
      .then((d) => setListings(d.listings))
      .catch((e) => { if (!authRedirect(e)) setError(errorText(e)); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const setSaved = (id: number, saved: boolean) =>
    setListings((ls) => ls && ls.map((l) => (l.id === id ? { ...l, saved } : l)));

  // optimistic: flip now, roll back if the server says no
  async function toggle(l: Listing) {
    const next = !l.saved;
    setError("");
    setSaved(l.id, next);
    try {
      await apiPost(`/api/listings/${l.id}/${next ? "save" : "remove"}/`);
    } catch (e) {
      setSaved(l.id, !next);
      if (!authRedirect(e)) setError(errorText(e));
    }
  }

  return (
    <div className="listings-page">
      <header className="listings-header">
        <h1>Job Feed</h1>
        <Link to="/saved">Saved Jobs</Link>
      </header>
      <FilterMenu active={filters !== null} onApply={setFilters} onReset={() => setFilters(null)} />
      {error && <p role="alert" className="listings-error">{error}</p>}
      {listings === null && !error && <p role="status">Loading jobs…</p>}
      {listings?.length === 0 && <p>{filters ? "No listings match these filters." : "No listings yet."}</p>}
      <ul className="listings-list">
        {listings?.map((l) => (
          <li key={l.id} className="card listing">
            <div>
              <h3>{l.title}</h3>
              <p>{l.company}</p>
              <JobDetails listing={l} />
            </div>
            <div className="listing-actions">
              <CredScore listing={l} />
              <button
                type="button"
                className="bookmark-button"
                aria-label={l.saved ? "Remove bookmark" : "Bookmark listing"}
                aria-pressed={l.saved}
                onClick={() => toggle(l)}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" fill={l.saved ? "currentColor" : "none"} aria-hidden="true">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                </svg>
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
