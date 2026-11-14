# Pathfinder (Team 2)
CS 4300/5300 Fall 2026, Team 2 group project

Pathfinder helps job seekers find listings, save the ones they like, and keep track of their search.

**Live site:** https://pathfinder-team2.up.railway.app

**Built with:** Django (backend and pages), React + TypeScript (frontend), PostgreSQL (production database), deployed on Railway.

## Documentation

- `docs/architecture/`: architecture notes and diagrams (system design, data flow, DB schema).
- `docs/agents/`: AI agent tooling: `AGENTS.md` (scoped agent rules, applies only within this
  directory, do not move or duplicate elsewhere), `context/` (project/architecture/workflow
  context the rules point at).
- `docs/branch-naming.md`: story branch naming convention.
- `docs/ai-authorship.md`: commit trailer convention for AI-assisted work.

Add docs as sprints produce them. Keep diagrams as source (Mermaid/PlantUML/.drawio) plus rendered output, not images alone.

## Running the project locally

1. Turn on your Python virtual environment
2. Install the backend packages: `pip install -r backend/requirements.txt`
3. Create a file `backend/.env` with this one line: `DATABASE_URL=sqlite:///db.sqlite3`
4. Set up the database:
   - `cd backend`
   - `python manage.py migrate`
   - `python manage.py createsuperuser`
5. Start the server: `python manage.py runserver`
In a second terminal, run npm ci (if first time running), then npm run dev, and visit http://localhost:5173/
6. 7. Open any of the pages below

**On DevEdu:** start the server with `python manage.py runserver 0.0.0.0:3000` instead,
and open your DevEdu app link (with the page address at the end) instead of localhost.

### Pages

| Page | Address | What it does |
|---|---|---|
| Sign up | `/accounts/signup/` | Create a new account |
| Log in | `/accounts/login/` | Log in as any user |
| Job feed | `/feed/` | See listings and bookmark them |
| Resume upload | `/resumes/upload/` | Upload a PDF or Word resume |
| Alerts | Alerts tab in the React app | Create, edit, pause, and delete job alerts |
| Notification history | Notification History tab in the React app | See past alerts and the listings that triggered them |
| Admin | `/admin/` | Add listings and manage users (superusers only) |
| Saved Jobs | `/saved/` | See all the listings you bookmarked in one place |

### Running the tests

`cd backend`, then `python manage.py test`

To run the Behave (BDD) scenarios:
`cd backend`, then `python manage.py behave`

To check test coverage:
`coverage run manage.py test`, then `coverage report`

Tests also run automatically on GitHub (GitHub Actions) for every push and pull request.

## Features

### US1.1: Sign up
New users can create an account at `/accounts/signup/`. Weak passwords (too short, too common,
or all numbers) are rejected. After signing up, users are logged in and sent to step 2.

### US1.2 / US1.3: Profile step and email verification
Step 2 asks for first name, last name and email (one account per email, ignoring case).
Step 3 emails a 6-digit code that works for 10 minutes; 5 wrong guesses lock it, and
"Resend code" sends a new one at most once a minute. Until both steps are done, the site
sends the user back to the step they owe, and the `/api/` endpoints refuse them.
If `EMAIL_HOST` is not set in prod, step 3 is skipped so new users don't get stuck.

### US2.1: Resume upload
Logged-in users can upload a resume (PDF, DOC, or DOCX, up to 5 MB) at `/resumes/upload/`.
Each user only sees their own uploads.

### US2.2: AI resume feedback
Logged-in users can request AI feedback for one of their uploaded resumes
The feedback page provides simple suggestions about what could be improved
Users can only request feedback for resumes they own

### US3.1: Credibility score
Each listing can have a credibility score, added on lisitng creation

### US3.2: Credibility Reasons
Each credibility score has reasons attached to it that can be seen by hovering over it.

### US3.3: Filters and Sorting
Listings can be filtered and sorted by different variables

### US4.1: Bookmark a listing
On the job feed (`/feed/`), each listing has a bookmark icon. Clicking it saves the listing,
and the icon fills in to show it's bookmarked. Clicking it again removes the bookmark.

### US4.2: Saved Jobs Page
Logged-in users can see all their bookmarked listings at `/saved/`, or by clicking the
"Saved Jobs" link at the top of the job feed. Each user only sees their own bookmarks.
If nothing is saved yet, the page shows "You haven't saved any jobs yet."

### US4.3: Remove a bookmark
Each job on the Saved Jobs page has a **Remove** button. Clicking it removes the bookmark
and keeps you on the Saved Jobs page, so the list only shows jobs you still want.

### US4.4: Private notes on a saved job
Each job on the Saved Jobs page has a note box. Type why you saved the job and click
**Add note**. You can add as many notes as you want, and each one has a small **×** to
delete it. Notes are saved on your bookmark, so only you can see them.

### US4.5: Application status on a saved job
Each job on the Saved Jobs page has a **status bar** above the note box: Saved, Applied,
Interviewing, Offer, or Rejected. Click one to set it. The current status is highlighted
in its own color. New saved jobs start as Saved.
Each note also shows the date and time it was written.

### US4.6: Filter saved jobs by status
The **Show** dropdown at the top of the Saved Jobs page shows only the jobs with that
status (for example, only **Applied**), so you can see which applications need follow-up.

### Real job listings (JobDataLake)
The job feed shows real tech jobs from companies across the US, pulled from the
[JobDataLake API](https://jobdatalake.com). Each job shows its location, whether it's
remote, hybrid, or on-site, and an **Apply** link to the company's page.
Import new jobs with `python manage.py import_jobs --limit 20` (from `backend`).
Each run uses **1 API credit**, no matter how many jobs come back, and jobs already
saved are skipped. Options: `--query` (keywords, default any), `--function`
(job type, default `eng`; use `""` for all), and `--limit` (1–100).
The key goes in `backend/.env` as `JOBDATALAKE_API_KEY=...` and is **never committed**.

### US5.1–US5.6: Job alerts
Logged-in users can create alerts from keywords, location, or job type on the Alerts page,
choose email or in-app notifications, pick instant or daily delivery, and pause, edit, or
delete alerts. The Notification History page lists past alerts and the listings that
triggered them. Matching runs with `python manage.py run_alert_matching` (schedule it hourly).
Email alerts need the email settings below.

## Azure deployment (gateway -> web + api)

All UI is React (`frontend/`), served by `app-pathfinder-prod-web` (`pm2 serve --spa`). The public
origin is the nginx gateway (`app-pathfinder-prod-gateway`, `path-finders.app`), which sends only
`/api/`, `/admin/`, `/static/` and `/media/` to Django (`app-pathfinder-prod-api`) and everything
else to the React app, so `/login`, `/feed`, `/saved` and `/resumes/...` are client-side routes.
Every Django JSON endpoint must live under `/api/`. Infra is in `infra/terraform`; deploys run from
`.github/workflows/deploy.yml` on pushes to `main`. In local dev, Vite proxies the same prefixes to
`localhost:8000` (`API_ORIGIN` overrides it).

## Deployment settings (Railway)

> ⚠️ **Set these on the Railway backend service.** The backend refuses to start without
> `SECRET_KEY`. Without the email settings it still starts, but **email alerts are only
> written to the server log, not sent**, and a warning is printed at startup.

| Variable | Required? | Example | Purpose |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | long random string | Django signing key |
| `ALLOWED_HOSTS` | **Yes** | `pathfinder-team2.up.railway.app` | Domains the backend answers for |
| `DATABASE_URL` | **Yes** | `postgres://user:pass@host:5432/db` | Production database |
| `EMAIL_HOST` | For sign-up codes and email alerts | `smtp.gmail.com` | SMTP server. Leave unset to log emails instead of sending |
| `EMAIL_HOST_USER` | For email alerts | `alerts@yourdomain.com` | SMTP login |
| `EMAIL_HOST_PASSWORD` | For email alerts | app password | SMTP password (use an app password, never a personal one) |
| `DEFAULT_FROM_EMAIL` | Recommended | `Pathfinder <alerts@yourdomain.com>` | "From" address on alert emails (defaults to `EMAIL_HOST_USER`) |
| `EMAIL_PORT` | Optional | `587` | Defaults to 587 |
| `EMAIL_USE_TLS` | Optional | `True` | Defaults to True |
| `JOBDATALAKE_API_KEY` | For real job listings | your JobDataLake key | Lets `python manage.py import_jobs` fetch jobs (1 credit per run) |

> ⚠️ **Alerts only fire when the matching job runs.** Nothing schedules it automatically yet.
> Add a Railway cron job (e.g. every hour, `0 * * * *`) that runs
> `python manage.py run_alert_matching` with the same variables as the backend.

See `.env.example` for the full list used by Docker Compose.

## AI Usage Disclosure

This section records where and when team members used AI assistance: the tool used, what it helped with, and how the result was used.

### Team Member Disclosures

| Name | Tool | Used For | How It Was Used |
|---|---|---|---|
| Dominick | Claude (Anthropic) | Generating ideas for decomposed user stories (Section 3.2), including candidate stories for US3, US4, and US5. | Used as a starting point; the team reviewed, discussed, and edited before finalizing |
| Seth | Claude (Anthropic) | Generating the images used in the Lo-Fi UI Alignment section (Section 3.3). | Used as a starting point, then adjusted by the team |
| Nicole | Claude (Anthropic) | Generating ways to word the Gherkin Acceptance Criteria | Used as a starting point, then adjusted by the team |
| Riley | Claude (Anthropic) | Templating [specify: e.g., the document/section structure or formatting and grammar] | Used as a starting template, then filled in and edited by the team |
| Nicole | Claude (Anthropic) | US4.1 bookmark feature: models, views, template, CSS, tests, README setup steps, DevEdu setup help | Used as a starting point; I reviewed, tested, and edited the code |
| Seth | Codex (OpenAI) | Deployment planning, Railway configuration, Docker/Nginx gateway, GitHub Actions CI, and gateway test troubleshooting | Used for guidance and initial code suggestions, then I reviewed, tested, and committed the final work |
| Dominick | Claude (Anthropic) | US1.1 sign-up page: view, sign-up and login templates, tests | Used as a starting point; I reviewed, tested, edited, and committed the code |
| Seth | Codex (OpenAI) | US2.1 resume upload model, form, view, URLs, template, testing, and troubleshooting | Used for guidance and initial code suggestions, then I reviewed, tested, and committed the final work |
| Riley | Claude (Anthropic) | US5.1–US5.6 alerts: models, API, alert matching command, email delivery, Alerts and Notification History pages, tests, design and plan docs | Used to draft and review the code; I reviewed, tested, edited, and committed the final work |
| Nicole | Claude (Anthropic) | Saved Jobs page: view, URL, template, Saved Jobs link on feed, unit tests, Behave setup and scenario, coverage setup, README updates, local and DevEdu setup help | Used as a starting point; I ran the tests first to confirm they failed (TDD), asked for explanations of each piece, adjusted tests to match our team's data, checked the page in the browser, and committed the final work |
| Seth | Codex (OpenAI) | US2.2 AI resume feedback service, protected view, templates, Behave scenario, and Django tests | Used for guidance and initial code suggestions; I reviewed the code, tested the real website flow, and verified the full test suite and coverage |
| Nicole | Claude (Anthropic) | US4.3 remove bookmark: Remove button, redirect back to Saved Jobs, unit tests, Behave scenario, README | Used as a starting point; I wrote the tests first and confirmed they failed (TDD), checked the page in the browser, and committed the final work |
| Nicole Vance | Claude (Anthropic) | US4.4 private notes: Note model and migrations, add and delete note views, URLs, two-column Saved Jobs layout, unit tests, Behave scenario, README | Used as a starting point; I wrote the tests first and confirmed they failed (TDD), changed the design to allow multiple notes with a delete x, checked the page in the browser, and committed the final work |
| Seth | Codex (OpenAI) | US2.6 resume replacement and deletion API, React controls, unit tests, behavior scenarios, styling, and troubleshooting | Used for guidance and code suggestions; I reviewed each change, tested the complete feature in the browser, and ran the automated tests |
| Dominick | Claude (Anthropic) | US1.2 profile step after sign-up: profile form, step 2 view, URL, sign-up template changes, tests | Used as a starting point; I reviewed, tested, edited, and committed the code |
| Dominick | Claude (Anthropic) | US1.2 review fixes: middleware that sends new users back to step 2 until it's done, duplicate-email check, tests | Used as a starting point; I reviewed, tested, edited, and committed the code |
| Dominick | Claude (Anthropic) | US1.3 email verification: code model and migration, emailed 6-digit code, step 3 verify view, middleware check for unverified users, tests | Used as a starting point; I reviewed, tested, edited, and committed the code |
| Nicole | Claude (Anthropic) | Real job listings from JobDataLake: Listing fields and migration, API client, import_jobs command, tech-job filter, location and Apply link in React, unit tests, Behave scenario, README | Used as a starting point; I wrote the tests first and confirmed they failed (TDD), tested the real API (and fixed a blocked request by adding a User-Agent header), checked the feed in the browser, and committed the final work |
| Nicole | Claude (Anthropic) | US4.5 and US4.6: status bar on saved jobs, status filter, and note dates (Bookmark status field and migration, status API, filter, React status bar, unit tests, Behave scenarios, README) | Used as a starting point; I wrote the tests first and confirmed they failed (TDD), chose the status bar design, checked the Saved Jobs page in the browser, and committed the final work |
| [Add more as needed] | | | |

### Notes
All AI-assisted content was reviewed and edited by the team before inclusion in the final submission. No AI-generated content was submitted without team review.
