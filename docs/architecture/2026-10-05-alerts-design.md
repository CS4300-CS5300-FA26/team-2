# Alerts (US5.1-US5.6) Design

## Scope

Covers GitHub issues US5.1-US5.6 (search-criteria alerts, notification method,
frequency, pause/delete, edit, notification history). All assigned to
rbullock59 on branch `progress-tracking-alerts`.

Out of scope: Kanban pipeline. No user story exists yet for it even though it
shares the `progress-tracking-alerts` branch/slice name in architecture.md.
Needs its own stories and brainstorm before implementation.

## Dependency note

`listings.Listing` (on `bookmarking-search`, not yet merged to `main`) only has
`title` and `company`. Alert criteria include `location` and `job_type`, which
`Listing` has no fields for yet. Matching on those criteria is stubbed until
`Listing` grows those fields — see Matching Command below.

## Data model (`tracking` app)

```python
class Alert(models.Model):
    class NotifyMethod(models.TextChoices):
        EMAIL = "email"
        IN_APP = "in_app"

    class Frequency(models.TextChoices):
        INSTANT = "instant"
        DAILY = "daily"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    keywords = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    job_type = models.CharField(max_length=100, blank=True)
    notify_method = models.CharField(choices=NotifyMethod.choices, default=NotifyMethod.IN_APP)
    frequency = models.CharField(choices=Frequency.choices, default=Frequency.INSTANT)
    digest_time = models.TimeField(default=time(9, 0))  # used only when frequency == DAILY
    is_active = models.BooleanField(default=True)  # pause = False
    last_digest_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not (self.keywords or self.location or self.job_type):
            raise ValidationError("At least one of keywords, location, or job_type is required.")


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="notifications")
    listing = models.ForeignKey("listings.Listing", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    emailed_at = models.DateTimeField(null=True, blank=True)  # null = not yet included in an email
```

Blank criteria fields mean "don't filter on this dimension," not "match
nothing." At least one field must be set (enforced in `clean()` and mirrored
in the DRF serializer).

## API (`/api/alerts/`, `/api/notifications/`)

- `AlertViewSet(ModelViewSet)`, queryset scoped to `request.user`:
  - list/create/retrieve/update/destroy → US5.1 (create), US5.5 (edit), US5.4 (delete)
  - `PATCH {"is_active": false}` → pause (US5.4)
  - serializer validates at least one criteria field set; `notify_method`/`frequency` restricted to choices; `digest_time` only meaningful (but still storable) when `frequency == daily`
- `NotificationViewSet(ReadOnlyModelViewSet)`, queryset scoped to `request.user`, ordered `-created_at` → US5.6
- Cross-user access to another user's alert/notification id → 404 (object not in the scoped queryset), never 403, to avoid leaking existence.

## Matching command

`python manage.py run_alert_matching`, intended to run hourly via host cron
(no Celery/Redis — not in requirements.txt or docker-compose, and full
broker infra is unneeded for an hourly batch job).

1. For each `Alert` with `is_active=True`:
   - Build a `Listing` queryset: `created_at > alert's last-matched listing's created_at` (track via most recent `Notification.listing.created_at` for that alert, or `alert.created_at` if none yet), filtered by `icontains` on `keywords` against `title`/`company`. `location`/`job_type` are stored but not filtered on yet (`Listing` has no such fields) — `ponytail: location/job_type matching deferred, wire in once Listing gains those fields`.
   - Create a `Notification` row (read=False, emailed_at=None) per new match.
   - Wrap each alert's processing in try/except; log and continue on error so one bad alert doesn't abort the run.
2. Email delivery pass, only for `notify_method=email`:
   - `frequency=instant`: send one email per `Notification` just created this run; set `emailed_at=now`; on send failure, log and leave `emailed_at=null` so it retries next run.
   - `frequency=daily`: only when the current run's hour matches `digest_time`'s hour, gather all `Notification`s with `emailed_at=None` for that alert, send one digest email listing all of them, stamp `emailed_at=now` on all and `last_digest_sent_at=now` on the alert. Same retry-on-failure behavior.
3. In-app notifications (US5.6 history) are created immediately regardless of `frequency` — frequency only governs email cadence, not when a match becomes visible in notification history.

## Frontend

- **Alerts page**: list of the user's alerts (criteria, method, frequency, active/paused), a create/edit form (keywords/location/job_type/notify_method/frequency/digest_time-when-daily), pause toggle, delete with confirm.
- **Notification History page**: read-only list of `Notification`s, newest first, showing listing + which alert triggered it + timestamp.

## Testing

- Model: `Alert.clean()` rejects all-blank criteria; field defaults.
- API: CRUD scoped to owner; pause via PATCH; 404 on cross-user access; serializer validation 400s on bad criteria/enum/time values.
- Matching command: keyword match creates `Notification`; already-matched listings not re-matched; instant sends email immediately on match; daily only sends at the digest hour and batches multiple matches into one email; `is_active=False` alerts skipped; a raised exception in one alert's processing doesn't stop the run.
- Frontend: alert form create/edit/pause/delete round-trip against the API; notification history renders a list.

## Known gaps (explicitly out of scope here)

- Kanban pipeline (board model, drag-drop stages, auto-move on apply, undo) — no story written yet, needs its own brainstorm.
- `location`/`job_type` matching — blocked on `Listing` model gaining those fields (tracked in `bookmarking-search`).
- Celery/Redis — deferred; cron-invoked management command used instead. Revisit if instant delivery needs sub-hour latency.
