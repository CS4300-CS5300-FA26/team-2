# Code Standards

Stack-agnostic — applies regardless of which framework/language a slice
ends up using. Add a stack-specific section below once chosen; don't
replace these.

## General

- Keep modules small and single-purpose.
- Fix root causes, don't layer workarounds.
- Don't mix unrelated concerns in one component/route/function.
- No dead code, no commented-out code — delete it, git history has it.
- No speculative abstraction for hypothetical future requirements (YAGNI).

## Input and boundaries

- Validate and parse all external input (API requests, uploaded files,
  third-party API responses, user-entered text) at the boundary before any
  logic runs — never trust it implicitly deeper in the call stack.
- Sanitize anything that reaches an export, a rendered page, or a shell/SQL
  command (CSV export, SQL injection, XSS — see OWASP Top 10).
- Enforce auth and resource ownership before any mutation. A user only ever
  reads/mutates their own saved listings, pipeline records, notes, resumes.

## Error handling

- Handle errors that can actually occur (network/API failures, missing
  records, invalid input) — don't add handling for scenarios the type
  system or framework already rules out.
- Fail loudly in development, degrade gracefully in production where it
  matters (e.g. AI scoring unavailable shouldn't block saving a listing —
  see `architecture.md` invariant 3).
- Don't swallow errors silently; log or surface them.

## Secrets and config

- No credentials, API keys, or `.env` values committed — see `.gitignore`.
- Config/secrets read from environment, never hardcoded.

## Naming and structure

- Names say what something is/does — no abbreviations that need a comment
  to decode.
- One file organization scheme per slice, documented in that slice's own
  README once it exists; don't invent a second scheme inside a slice.

## Data and Storage

- Metadata (accounts, pipeline state, notes) belongs in PostgreSQL.
- Large generated content (resume files) belongs in file/blob storage, not
  the database directly.

## Testing

- Non-trivial logic (a branch, a loop, a parser, anything touching money,
  auth, or security) ships with at least one runnable test that fails if
  the logic breaks. Trivial one-liners don't need one.
- Tests live next to or in a path mirroring the code they cover — no
  separate untracked test scratch files.

## Comments

- Comment the why, not the what — a hidden constraint, a workaround for a
  specific bug, a non-obvious invariant. Skip comments that just restate
  the code.

## File Organization

- One top-level folder per feature slice, matching the slice branch names
  (`signup-user-management`, `file-upload-digitization`, `ai-intelligence`,
  `bookmarking-search`, `progress-tracking-alerts`) once code exists —
  exact internal layout is stack-dependent, fill in when chosen.
