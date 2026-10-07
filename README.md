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
| Admin | `/admin/` | Add listings and manage users (superusers only) |

### Running the tests

`cd backend`, then `python manage.py test`

Tests also run automatically on GitHub (GitHub Actions) for every push and pull request.

## Features

### US1.1: Sign up
New users can create an account at `/accounts/signup/`. Weak passwords (too short, too common,
or all numbers) are rejected. After signing up, users are logged in and sent to the job feed.

### US2.1: Resume upload
Logged-in users can upload a resume (PDF, DOC, or DOCX, up to 5 MB) at `/resumes/upload/`.
Each user only sees their own uploads.

### US3.1: Credibility score
Each listing can have a credibility score, added through the admin page.

### US4.1: Bookmark a listing
On the job feed (`/feed/`), each listing has a bookmark icon. Clicking it saves the listing,
and the icon fills in to show it's bookmarked. Clicking it again removes the bookmark.

## AI Usage Disclosure

This section records where and when team members used AI assistance: the tool used, what it helped with, and how the result was used.

### Team Member Disclosures

| Name | Tool | Used For | How It Was Used |
|---|---|---|---|
| Dominick | Claude (Anthropic) | Generating ideas for decomposed user stories (Section 3.2), including candidate stories for US3, US4, and US5. | Used as a starting point; the team reviewed, discussed, and edited before finalizing |
| Seth | Claude (Anthropic) | Generating the images used in the Lo-Fi UI Alignment section (Section 3.3). | Used as a starting point, then adjusted by the team |
| Nicole | Claude (Anthropic) | Generating ways to word the Gherkin Acceptance Criteria | Used as a starting point, then adjusted by the team |
| Riley | Claude (Anthropic) | Templating [specify: e.g., the document/section structure or formatting and grammar] | Used as a starting template, then filled in and edited by the team |
| Nicole Vance | Claude (Anthropic) | US4.1 bookmark feature: models,
