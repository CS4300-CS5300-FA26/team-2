import { useState } from "react";
import AlertsPage from "./pages/AlertsPage";
import NotificationHistoryPage from "./pages/NotificationHistoryPage";

export default function App() {
  const [tab, setTab] = useState<"alerts" | "history">("alerts");

  return (
    <main>
      <h1>Pathfinder</h1>
      <nav>
        <button type="button" onClick={() => setTab("alerts")}>Alerts</button>
        <button type="button" onClick={() => setTab("history")}>Notification History</button>
      </nav>
      {tab === "alerts" ? <AlertsPage /> : <NotificationHistoryPage />}
    </main>
  );
}
