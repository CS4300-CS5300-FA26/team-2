# Pathfinder

## Overview

Pathfinder brings job listings, AI credibility assessments, and application
tracking together in one web application. It addresses two problems college
students face when job hunting: questionable/scam listings, and scattered,
hard-to-track applications.

## Goals

1. Let a user browse job listings from external sources and see an AI
   credibility score with supporting reasons before applying.
2. Let a user track applications through a Kanban-style pipeline
   (Saved, Applied, Screening, Interviewing, Offer, Rejected) without manual
   data entry duplicating what they already did on the employer's site.
3. Proactively surface follow-up reminders and high-match/low-risk listings
   instead of requiring the user to check manually.

## Core User Flow

1. Browse/filter job listings (sourced from Remotive, stretch: additional
   sources).
2. Open a listing, read source evidence, review its AI credibility score and
   reasons (or "insufficient information").
3. Sign in, save the listing.
4. Click the external apply link — card auto-moves to "Applied" in the
   tracker (undoable).
5. Manage the application via the Kanban board: drag between stages, add
   notes, get reminders.
6. Return later to saved/application history.

## Features

### Credibility assessment (MVP)
- AI-generated credibility score + supporting reasons per listing, sourced
  from listing evidence via OpenAI API.
- Explicit "insufficient information" state when evidence doesn't support a
  confident score — never force a score.

### Application tracker (MVP)
- Kanban board: Saved, Applied, Screening, Interviewing, Offer, Rejected.
- Drag-and-drop stage transitions, async (no full page reload).
- Auto-transition to "Applied" on external apply-link click, with undo toast.
- `stage_updated_at` timestamp per card for audit/analytics.

### Data export & feedback (post-MVP, Epic 2)
- CSV/Excel export of full tracking history, CSV-injection-safe.
- Optional rejection survey (stage reached, ghosted vs. formal, notes) to
  feed drop-off analytics.

### Alerts (post-MVP, Epic 3)
- Inactivity/follow-up reminders (nightly job, configurable threshold).
- High-match (>85%) + low-risk (>90% trust) new-listing alerts, with
  instant/daily-digest/none frequency options.

## Scope

### In Scope (MVP)
- Browse/filter listings from one job source (Remotive).
- Credibility assessment with evidence and reasons.
- Save listings, Kanban tracking, status updates.
- Return to saved/application history.

### Out of Scope (MVP — stretch per sprint plan)
- Multiple job sources beyond Remotive (arbeitnow, USAJOBS, etc.)
- Google Calendar integration
- Resume advice / AI resume judging beyond parsing
- Multi-language support
- MFA, SSO (slated for Sprint 4)

## Success Criteria

1. A signed-in user can browse listings, see a credibility score with
   reasons (or an explicit "insufficient information" state), and save one.
2. Clicking the external apply link moves the card to "Applied" without a
   manual entry, and the user can undo it.
3. A user can drag a card across all six pipeline stages and the change
   persists (async, `stage_updated_at` updates).
