import { useEffect, useState } from "react";
import {
  Alert, AlertInput, createAlert, deleteAlert, fetchAlerts, updateAlert,
} from "../api/alerts";

const emptyForm: AlertInput = {
  keywords: "", location: "", job_type: "",
  notify_method: "in_app", frequency: "instant", digest_time: "09:00",
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [form, setForm] = useState<AlertInput>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = () => fetchAlerts().then(setAlerts).catch(() => setError("Failed to load alerts."));

  useEffect(() => {
    reload();
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (editingId !== null) {
        await updateAlert(editingId, form);
      } else {
        await createAlert(form);
      }
      setForm(emptyForm);
      setEditingId(null);
      reload();
    } catch {
      setError("Could not save alert. Check that at least one of keywords, location, or job type is set.");
    }
  };

  const startEdit = (alert: Alert) => {
    setEditingId(alert.id);
    setForm({
      keywords: alert.keywords, location: alert.location, job_type: alert.job_type,
      notify_method: alert.notify_method, frequency: alert.frequency, digest_time: alert.digest_time,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(emptyForm);
  };

  const togglePause = (alert: Alert) => updateAlert(alert.id, { is_active: !alert.is_active }).then(reload);

  const remove = (alert: Alert) => deleteAlert(alert.id).then(reload);

  return (
    <section>
      <h2>Alerts</h2>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={submit}>
        <label htmlFor="alert-keywords">Keywords</label>
        <input
          id="alert-keywords"
          placeholder="e.g. backend intern"
          value={form.keywords}
          onChange={(e) => setForm({ ...form, keywords: e.target.value })}
        />
        <label htmlFor="alert-location">Location</label>
        <input
          id="alert-location"
          placeholder="e.g. Remote"
          value={form.location}
          onChange={(e) => setForm({ ...form, location: e.target.value })}
        />
        <label htmlFor="alert-job-type">Job type</label>
        <input
          id="alert-job-type"
          placeholder="e.g. Internship"
          value={form.job_type}
          onChange={(e) => setForm({ ...form, job_type: e.target.value })}
        />
        <label htmlFor="alert-notify-method">Notify via</label>
        <select
          id="alert-notify-method"
          value={form.notify_method}
          onChange={(e) => setForm({ ...form, notify_method: e.target.value as Alert["notify_method"] })}
        >
          <option value="in_app">In-app</option>
          <option value="email">Email</option>
        </select>
        <label htmlFor="alert-frequency">Frequency</label>
        <select
          id="alert-frequency"
          value={form.frequency}
          onChange={(e) => setForm({ ...form, frequency: e.target.value as Alert["frequency"] })}
        >
          <option value="instant">Instant</option>
          <option value="daily">Daily digest</option>
        </select>
        {form.frequency === "daily" && (
          <>
            <label htmlFor="alert-digest-time">Digest time</label>
            <input
              id="alert-digest-time"
              type="time"
              value={form.digest_time}
              onChange={(e) => setForm({ ...form, digest_time: e.target.value })}
            />
          </>
        )}
        <button type="submit">{editingId !== null ? "Save" : "Create alert"}</button>
        {editingId !== null && (
          <button type="button" onClick={cancelEdit}>Cancel</button>
        )}
      </form>
      <ul>
        {alerts.map((alert) => (
          <li key={alert.id}>
            {alert.keywords || alert.location || alert.job_type} — {alert.notify_method}/{alert.frequency}{" "}
            {alert.is_active ? "(active)" : "(paused)"}
            <button type="button" onClick={() => startEdit(alert)}>Edit</button>
            <button type="button" onClick={() => togglePause(alert)}>
              {alert.is_active ? "Pause" : "Resume"}
            </button>
            <button type="button" onClick={() => remove(alert)}>Delete</button>
          </li>
        ))}
      </ul>
    </section>
  );
}
