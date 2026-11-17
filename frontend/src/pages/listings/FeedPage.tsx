import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost } from "../../api/client";
import { CredScore, Listing, errorText, useAuthRedirect, JobDetails, ReportReason } from "./shared";
import FilterMenu, { FeedFilters } from "./FilterMenu";
import "./listings.css";

export default function FeedPage() {
  const [listings, setListings] = useState<Listing[] | null>(null);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState<FeedFilters | null>(null);
  const authRedirect = useAuthRedirect();

  // Runs when filters change
  useEffect(() => {
    // Set query if filters applied
    const query = filters ? "?" + new URLSearchParams({
          sort_by: filters.sortBy,
          min_score: String(filters.minScore),
          max_score: String(filters.maxScore),
        }).toString()
      : "";
    setError("");
    apiGet<{ listings: Listing[] }>(`/api/listings/feed/${query}`)
      .then((d) => setListings(d.listings))
      .catch((e) => { if (!authRedirect(e)) setError(errorText(e)); });
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

  // Attempt to report a listing
  async function reportListing(id: number, reason: string): Promise<boolean> {
    setError("");
    try {
      await apiPost(`/api/listings/${id}/report/`, { reason });
      return true;
    } catch (e) {
      if (!authRedirect(e)) setError(errorText(e));
      return false;
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
          <ListingCard l={l} toggle={toggle} report={reportListing}/>
        ))}
      </ul>
    </div>
  );
}

// Only way I can have multiple parameters in the ListingCard component :sob:
interface ListingCardProps {
  l: Listing,
  toggle: Function,
  report: (id: number, reason: string) => Promise<boolean>
}

/*
Moved this to a seperate component so that I can tell specifically which Listing is being reported for US3.4 - Josh
I tried so hard to not have to make changes this big to it, but this is the best way I could see.
tbf this does also help with SRP
*/
function ListingCard({ l, toggle, report }: ListingCardProps) {

  // Change card in reporting stages
  const [isBeingReported, setIsBeingReported] = useState(false);
  const [isReported, setIsReported] = useState(false);

  // Tie what backend knows to what frontend shows
  const REPORT_OPTIONS: [ReportReason, string][] = [
    ["fake", "This Listing Seems Fake or a Scam"],
    ["inappropriate", "This listing is inappropriate"],
    ["harmful-or-illegal", "This listing is for a harmful or illegal job."],
  ]

  // Shows after submit report button is pressed
  if (isReported) {
    return (
      <li key={l.id} className="card listing">
        <p>Thank you for your report!</p>
      </li>
    )
  }
  // Shows normally
  else if (!isBeingReported) {
    return (
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

              <div className="report-button">
                <button
                  type="button"
                  className="report-button"
                  aria-label="Report listing"
                  onClick={() => setIsBeingReported(true)}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 13v8q0 .425-.288.713T6 22t-.712-.288T5 21V4q0-.425.288-.712T6 3h13.525q.275 0 .488.125t.337.325t.162.438t-.062.487L19 8l1.45 3.625q.1.25.063.488t-.163.437t-.337.325t-.488.125zm0-2h11.05l-.9-2.25Q17 8.4 17 8t.15-.75l.9-2.25H7zm0 0V5z"/>
                  </svg>
                </button>
              </div>

            </div>
      </li>
    );
  }
  // Shows when flag button is pressed
  else if (isBeingReported) {
    return (
      <li key={l.id} className="card listing">
        <h3>Please select a report reason:</h3>
        <form
          className="report-form"
          onSubmit={async (e) => {
            e.preventDefault();
            const reason = new FormData(e.currentTarget).get("report-for");
            if (typeof reason !== "string") return;
            if (await report(l.id, reason)) {
              setIsBeingReported(false);
              setIsReported(true);
            }
          }}
        >
          <div className="report-reason-response">
            <fieldset>
              {REPORT_OPTIONS.map(([value, label]) => (
                <label key={value} className="report-sort-option">
                  {label}
                  <input
                    type="radio"
                    name="report-for"
                    value={value}
                    required
                  >
                  </input>
                </label>
              ))}
            </fieldset>
          </div>
          <button
            type="submit"
            className="report-submit"
          >
            Submit Report
          </button>
        </form>
      </li>
    );
  }
}
