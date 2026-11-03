import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import "./resumes.css";
import { requestFeedback, type ApiError, type Feedback } from "./http";

export default function FeedbackPage() {
  const { id } = useParams();
  const [data, setData] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const started = useRef<string>();

  useEffect(() => {
    if (!id || started.current === id) return; // StrictMode would otherwise bill the AI twice
    started.current = id;
    requestFeedback(Number(id))
      .then(setData)
      .catch((e: ApiError) => {
        if (e.status === 401) {
          window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname)}`);
        } else {
          setError(e.status === 404 ? "We couldn't find that resume." : e.message);
        }
      });
  }, [id]);

  return (
    <main className="resumes-page">
      <Link to="/resumes/upload">&larr; Back to your resumes</Link>
      <section className="card">
        <h1>AI resume feedback</h1>
        {data && <p className="muted">Feedback for {data.resume.name}</p>}

        {error && (
          <p role="alert" className="resumes-error">
            {error}
          </p>
        )}

        {!data && !error && (
          <div aria-busy="true" role="status">
            <span className="sr-only">Generating feedback, this can take a few seconds</span>
            {[90, 75, 85, 60].map((w) => (
              <div key={w} className="skeleton" style={{ width: `${w}%`, height: 20, marginBottom: 14 }} />
            ))}
          </div>
        )}

        {data && (
          <>
            <h2>Suggestions</h2>
            <ol className="suggestions">
              {data.suggestions.map((s, i) => (
                <li key={i}>{s.replace(/^\s*(?:\d+[.)]|[-*•])\s*/, "")}</li>
              ))}
            </ol>
            <p className="resumes-warn">
              AI feedback can make mistakes, so review each suggestion before changing your resume.
            </p>
          </>
        )}
      </section>
    </main>
  );
}
