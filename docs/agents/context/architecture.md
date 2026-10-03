# Architecture Context

## Stack

| Layer      | Technology                        | Role                                   |
| ---------- | ---------------------------------- | --------------------------------------- |
| Framework  | [TBD — not yet chosen by team]     | [Role]                                  |
| UI         | [TBD]                               | [Role]                                  |
| Auth       | [TBD — US1.x covers password, email verification, MFA, SSO] | [Role] |
| Database   | SQL (PostgreSQL, per epics)         | Accounts, saved listings, application/pipeline history |
| Listings   | Remotive API                        | Job listings + original source links (stretch: arbeitnow, USAJOBS) |
| AI scoring | OpenAI API                          | Credibility assessments with supporting reasons |
| Background jobs | [TBD — epics reference a nightly Celery worker for inactivity reminders; confirm if Celery or an alternative] | Alert/reminder checks |

## System Boundaries

Maps to the 5 long-lived feature-slice branches (see `/CONTRIBUTING.md`):

- `signup-user-management` — accounts, authn/authz (US1.x)
- `file-upload-digitization` — resume/CV upload, parsing, versions (US2.x)
- `ai-intelligence` — credibility scoring, match scoring, listing reasons (US3.x)
- `bookmarking-search` — browse/filter listings, bookmarking, home display (US4.x)
- `progress-tracking-alerts` — Kanban pipeline, notes, alerts/notifications (US5.x)

## Storage Model

- **Database (PostgreSQL)**: accounts, saved listings, application/pipeline
  records (including `stage_updated_at`), notes, alert preferences.
- **Blob/File Storage**: [TBD — resume/CV files from Epic/slice 2; confirm
  provider once file-upload-digitization work starts]

## Auth and Access Model

- Every user signs in (US1.x: password, email verification, MFA, SSO —
  phased across sprints per sprint plan).
- Every application/pipeline record and saved listing is owned by a single
  user.
- Only the owning user can read or mutate their saved listings, notes, and
  pipeline state.

## Invariants

1. A credibility score is never fabricated when evidence is insufficient —
   surface "insufficient information" instead.
2. Stage transitions always update `stage_updated_at`.
3. Clicking a listing's external apply link does not block on — or depend
   on — the AI scoring pipeline; application tracking must work even if
   scoring is degraded/unavailable.
4. [Additional invariants — add as architecture decisions are made]
