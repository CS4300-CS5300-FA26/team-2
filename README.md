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
6. Log in at http://localhost:8000/admin/ with your superuser and add a few listings
7. Open any of the pages below

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
or all numbers) are rejected. After signing up, users are logged in and sent to the job feed.

### US2.1: Resume upload
Logged-in users can upload a resume (PDF, DOC, or DOCX, up to 5 MB) at `/resumes/upload/`.
Each user only sees their own uploads.

### US2.2: AI resume feedback
Logged-in users can request AI feedback for one of their uploaded resumes
The feedback page provides simple suggestions about what could be improved
Users can only request feedback for resumes they own

### US3.1: Credibility score
Each listing can have a credibility score, added through the admin page.

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

### US5.1–US5.6: Job alerts
Logged-in users can create alerts from keywords, location, or job type on the Alerts page,
choose email or in-app notifications, pick instant or daily delivery, and pause, edit, or
delete alerts. The Notification History page lists past alerts and the listings that
triggered them. Matching runs with `python manage.py run_alert_matching` (schedule it hourly).
Email alerts need the email settings below.

## Deployment settings (Railway)

> ⚠️ **Set these on the Railway backend service.** The backend refuses to start without
> `SECRET_KEY`. Without the email settings it still starts, but **email alerts are only
> written to the server log, not sent**, and a warning is printed at startup.

| Variable | Required? | Example | Purpose |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | long random string | Django signing key |
| `ALLOWED_HOSTS` | **Yes** | `pathfinder-team2.up.railway.app` | Domains the backend answers for |
| `DATABASE_URL` | **Yes** | `postgres://user:pass@host:5432/db` | Production database |
| `EMAIL_HOST` | For email alerts | `smtp.gmail.com` | SMTP server. Leave unset to log emails instead of sending |
| `EMAIL_HOST_USER` | For email alerts | `alerts@yourdomain.com` | SMTP login |
| `EMAIL_HOST_PASSWORD` | For email alerts | app password | SMTP password (use an app password, never a personal one) |
| `DEFAULT_FROM_EMAIL` | Recommended | `Pathfinder <alerts@yourdomain.com>` | "From" address on alert emails (defaults to `EMAIL_HOST_USER`) |
| `EMAIL_PORT` | Optional | `587` | Defaults to 587 |
| `EMAIL_USE_TLS` | Optional | `True` | Defaults to True |

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
| [Add more as needed] | | | |

### Notes
All AI-assisted content was reviewed and edited by the team before inclusion in the final submission. No AI-generated content was submitted without team review.
