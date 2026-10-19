import { useEffect, useState } from "react";
import { fetchNotifications, Notification } from "../api/alerts";

export default function NotificationHistoryPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNotifications().then(setNotifications).catch(() => setError("Failed to load notification history."));
  }, []);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  if (notifications.length === 0) {
    return <p>No notifications yet.</p>;
  }

  return (
    <section>
      <h2>Notification History</h2>
      <ul>
        {notifications.map((n) => (
          <li key={n.id}>
            {new Date(n.created_at).toLocaleString()} — {n.listing_title} at {n.listing_company}
          </li>
        ))}
      </ul>
    </section>
  );
}
