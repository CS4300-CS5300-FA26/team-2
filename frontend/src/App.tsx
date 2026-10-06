import { useEffect, useState } from "react";
import UnderConstruction from "./pages/UnderConstruction";

const STUB_PAGES: Record<string, string> = {
  signup: "Sign Up / Account",
  resumes: "Resume Upload",
  "ai-intelligence": "AI Credibility Scoring",
  alerts: "Progress Tracking & Alerts",
};

function currentHash() {
  return window.location.hash.replace("#", "") || "home";
}

export default function App() {
  const [tab, setTab] = useState(currentHash());

  useEffect(() => {
    const onHashChange = () => setTab(currentHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return (
    <main>
      <h1>Pathfinder</h1>
      <nav>
        <a href="#home">Home</a>
        {" | "}
        <a href="/feed/">Bookmarking &amp; Search</a>
        {" | "}
        <a href="/accounts/login/">Log in</a>
        {" | "}
        <a href="#signup">Sign Up / Account</a>
        {" | "}
        <a href="#resumes">Resume Upload</a>
        {" | "}
        <a href="#ai-intelligence">AI Credibility</a>
        {" | "}
        <a href="#alerts">Progress Tracking &amp; Alerts</a>
      </nav>
      {tab === "home" && <p>Frontend scaffold is up. Backend API lives at /api/.</p>}
      {tab in STUB_PAGES && <UnderConstruction title={STUB_PAGES[tab]} />}
    </main>
  );
}
