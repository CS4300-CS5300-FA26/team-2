# Contributing

## Branch model

- `main` — protected. Future CI/CD prod branch. Requires a PR with 1 approving review to merge. No direct pushes, no force-push, no deletion. Protection applies to admins too.
- 5 long-lived feature-slice branches off `main`, one per epic area:
  - `signup-user-management` — Authn/Authz, accounts (US1.x)
  - `file-upload-digitization` — resume/CV upload and parsing (US2.x)
  - `ai-intelligence` — credibility scoring, match scoring, scam detection (US3.x)
  - `bookmarking-search` — job search, bookmarking, home display (US4.x)
  - `progress-tracking-alerts` — Kanban pipeline tracking, alerts/notifications (US5.x)
- Story branches cut from the relevant slice branch, PR back into that slice branch. See [docs/branch-naming.md](docs/branch-naming.md) for naming.
- Slice branches PR into `main` when their work is stable/release-ready.

## PRs

- Use the PR template (auto-applied). Link the story (US#.#), disclose any AI assistance, note how you tested it.
- 1 approving review required before merge into `main`. Slice branches don't currently enforce this but review before merging into them is still expected practice.
- Keep PRs scoped to one story where possible.

## Commits

- Imperative mood ("Add", "Fix", not "Added"/"Fixes").
- Reference the story id when relevant (`US2.1: add resume upload endpoint`).
- GPG-signed commits required on `main`-bound work.
- AI assistance in authorship: see [docs/ai-authorship.md](docs/ai-authorship.md) for the commit trailer format.

## AI usage

Per the team's AI Usage Disclosure practice (see `README.md`), disclose AI assistance in the PR template's disclosure section for every PR, not just the shared doc, and in commit trailers per [docs/ai-authorship.md](docs/ai-authorship.md).
