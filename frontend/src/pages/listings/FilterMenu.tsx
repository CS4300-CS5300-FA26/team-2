import { useRef, useState } from "react";

// US3.3: sort + score-range filter dropdown for the job feed.
// Ported from the old Django template (feed.html); the choices match the
// ?sort_by / ?min_score / ?max_score query params of GET /api/listings/feed/.
export type SortBy = "date-desc" | "date-asc" | "score-desc" | "score-asc";
export type FeedFilters = { sortBy: SortBy; minScore: number; maxScore: number };

export const DEFAULT_FILTERS: FeedFilters = { sortBy: "date-desc", minScore: 0, maxScore: 100 };

const SORT_OPTIONS: [SortBy, string][] = [
  ["date-desc", "Date posted (desc)"],
  ["date-asc", "Date posted (asc)"],
  ["score-desc", "Score (desc)"],
  ["score-asc", "Score (asc)"],
];

type Props = {
  onApply: (filters: FeedFilters) => void;
  onReset: () => void;
  active: boolean; // true while filters are applied, to show the Reset button
};

export default function FilterMenu({ onApply, onReset, active }: Props) {
  const [draft, setDraft] = useState<FeedFilters>(DEFAULT_FILTERS);
  const detailsRef = useRef<HTMLDetailsElement>(null);

  const close = () => {
    if (detailsRef.current) detailsRef.current.open = false;
  };

  return (
    <div className="filter-menu">
      <details ref={detailsRef}>
        <summary className="filter-button" aria-label="Filter and sort listings">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M14 20.5H10C9.80189 20.4974 9.61263 20.4176 9.47253 20.2775C9.33244 20.1374 9.25259 19.9481 9.25 19.75V12L3.9 4.69C3.81544 4.58007 3.76395 4.44832 3.75155 4.31018C3.73915 4.17204 3.76636 4.03323 3.83 3.91C3.89375 3.78712 3.98984 3.68399 4.10792 3.61173C4.226 3.53947 4.36157 3.50084 4.5 3.5H19.5C19.6384 3.50084 19.774 3.53947 19.8921 3.61173C20.0101 3.68399 20.1062 3.78712 20.17 3.91C20.2336 4.03323 20.2608 4.17204 20.2484 4.31018C20.236 4.44832 20.1846 4.58007 20.1 4.69L14.75 12V19.75C14.7474 19.9481 14.6676 20.1374 14.5275 20.2775C14.3874 20.4176 14.1981 20.4974 14 20.5ZM10.75 19H13.25V11.75C13.2492 11.5907 13.302 11.4357 13.4 11.31L18 5H6L10.62 11.31C10.718 11.4357 10.7708 11.5907 10.77 11.75L10.75 19Z" />
          </svg>
        </summary>

        <form
          className="filter-dropdown"
          onSubmit={(e) => {
            e.preventDefault();
            onApply(draft);
            close();
          }}
        >
          <fieldset className="filter-section">
            <legend>Sort listings by:</legend>
            {SORT_OPTIONS.map(([value, label]) => (
              <label key={value} className="filter-sort-option">
                {label}
                <input
                  type="radio"
                  name="sort_by"
                  value={value}
                  checked={draft.sortBy === value}
                  onChange={() => setDraft({ ...draft, sortBy: value })}
                />
              </label>
            ))}
          </fieldset>

          <div className="filter-section">
            <span className="filter-legend">Only show listings that have score in range:</span>
            <div className="filter-sliders">
              {/* each slider is capped by the other one, so min can never pass max */}
              <input
                type="range"
                aria-label="Minimum score"
                className="filter-min"
                min={0}
                max={100}
                value={draft.minScore}
                onChange={(e) => setDraft({ ...draft, minScore: Math.min(Number(e.target.value), draft.maxScore) })}
              />
              <input
                type="range"
                aria-label="Maximum score"
                className="filter-max"
                min={0}
                max={100}
                value={draft.maxScore}
                onChange={(e) => setDraft({ ...draft, maxScore: Math.max(Number(e.target.value), draft.minScore) })}
              />
            </div>
            <div className="filter-range-values">
              <output>{draft.minScore}</output>
              <output>{draft.maxScore}</output>
            </div>
          </div>

          <div className="filter-actions">
            <button type="submit">Apply</button>
            {active && (
              <button
                type="button"
                onClick={() => {
                  setDraft(DEFAULT_FILTERS);
                  onReset();
                  close();
                }}
              >
                Reset
              </button>
            )}
          </div>
        </form>
      </details>
    </div>
  );
}
