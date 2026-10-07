# team-2
CS 4300/5300 Fall 2026 — Team 2 group project

## Documentation

- `architecture/` — architecture notes, diagrams (system design, data flow, DB schema).
- `agents/` — AI agent tooling: `AGENTS.md` (scoped agent rules, applies only within this
  directory — do not move or duplicate elsewhere), `context/` (project/architecture/workflow
  context the rules point at).
- `branch-naming.md` — story branch naming convention.
- `ai-authorship.md` — commit trailer convention for AI-assisted work.

Add docs as sprints produce them. Keep diagrams as source (Mermaid/PlantUML/.drawio) plus rendered output, not images alone.

# AI Usage Disclosure — Sprint 0-2

This document records where and when team members used AI assistance: the tool used, what it helped with, and how the result was used.

## Team Member Disclosures

| Name | Tool | Used For | How It Was Used |
|---|---|---|---|
| Dominick | Claude (Anthropic) | Generating ideas for decomposed user stories (Section 3.2), including candidate stories for US3, US4, and US5. | Used as a starting point; the team reviewed, discussed, and edited before finalizing |
| Seth | Claude (Anthropic) | Generating the images used in the Lo-Fi UI Alignment section (Section 3.3). | Used as a starting point, then adjusted by the team |
| Nicole | Claude (Anthropic) |Generating way to word the Gherkin Acceptance Criterias | Used as a starting point, then adjusted by the team |
| Riley | Claude (Anthropic) | Templating [specify: e.g., the document/section structure or formatting and grammar] | Used as a starting template, then filled in and edited by the team |
| Nicole Vance | Claude (Anthropic) | US4.1 bookmark feature: models, views, template, CSS, tests, README setup steps, DevEdu setup help | Used as a starting point; I reviewed, tested, and edited the code |
| Seth | Codex (OpenAI) | Deployment planning, Railway configuration, Docker/Nginx gateway, GitHub Actions CI, and gateway test troubleshooting | Used for guidance and initial code suggestions, then I reviewed, tested, and committed the final work ||
| Dominick | Claude (Anthropic) | US1.1 sign-up page: view, sign-up and login templates, tests | Used as a starting point; I reviewed, tested, edited, and committed the code |
| Seth | Codex (OpenAI) | US2.1 resume upload model, form, view, URLs, template, testing, and troubleshooting | Used for guidance and initial code suggestions, then I reviewed, tested, and committed the final work |
| [Add more as needed] | | | |

## Notes
All AI-assisted content was reviewed and edited by the team before inclusion in the final submission. No AI-generated content was submitted without team review.

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
7. Open http://localhost:8000/feed/ to see the job feed. Regular users log in at http://localhost:8000/accounts/login/

**On DevEdu:** start the server with `python manage.py runserver 0.0.0.0:3000` instead,
and open your DevEdu app link (ending in `/admin/` or `/feed/`) instead of localhost.

To run the tests: `cd backend`, then `python manage.py test`

## US4.1 — Bookmark a listing

On the job feed (`/feed/`), each listing has a bookmark icon. Clicking it saves the listing,
and the icon fills in to show it's bookmarked. Clicking it again removes the bookmark.
