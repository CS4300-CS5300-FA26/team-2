# Progress Tracker

Update this file after every meaningful implementation change.

## Current Phase

- Repo/branch scaffolding (pre-Sprint 1)

## Current Goal

- Finish repo maintenance: branch protection, CONTRIBUTING, agent context,
  graph-traversal tooling plan.

## Completed

- 5 long-lived feature-slice branches created off `main`.
- Branch protection rule defined for `main` (PR + 1 review + enforce_admins).

## In Progress

- Agent context files (this directory).

## Next Up

- Sprint 1 stories per sprint plan (US1.1, US1.2, US1.4, US2.1, US2.2,
  US2.4, US2.6, US4.2).

## Open Questions

- File/blob storage provider for resume uploads not yet chosen.
- Background job runner (Celery, per epics, or alternative) not confirmed.

## Architecture Decisions

- Backend: Django 5.x + DRF (Python 3.12). Frontend: React + TypeScript
  (Vite), separate SPA consuming the API over `/api/`. Deployment: Docker
  Compose + nginx, host-agnostic, TLS deferred until a domain exists. See
  `architecture.md` Stack table and Deployment section.

## Session Notes

- None yet.
