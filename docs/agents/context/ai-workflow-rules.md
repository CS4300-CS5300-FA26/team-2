# AI Workflow Rules

## Approach

Build Pathfinder incrementally, one user story at a time, against the
sprint plan. Context files define what to build and the current state of
progress — implement against these specs, don't infer or invent behavior.

## Scoping Rules

- Work on one story (US#.#) at a time, within one feature slice.
- Prefer small, verifiable increments over large speculative changes.
- Don't combine work across feature slices (`signup-user-management`,
  `file-upload-digitization`, `ai-intelligence`, `bookmarking-search`,
  `progress-tracking-alerts`) in a single implementation step — they're
  separate long-lived branches for a reason.

## When to Split Work

Split an implementation step if it combines:

- Work spanning more than one feature slice
- UI changes and background-job changes (e.g. Kanban UI + Celery reminder
  worker)
- Behavior not clearly defined in the context files or the story's
  acceptance criteria

If a change can't be verified end to end quickly, the scope is too broad —
split it.

## Handling Missing Requirements

- Don't invent product behavior not defined in the context files or the
  linked story's acceptance criteria.
- If a requirement is ambiguous, resolve it in the relevant context file
  before implementing.
- If a requirement is missing, add it as an open question in
  `progress-tracker.md` before continuing.

## Protected Files

Do not modify the following unless explicitly instructed:

- [e.g. generated UI library components]
- [e.g. third-party library internals]

## Keeping Docs in Sync

Update the relevant context file whenever implementation changes:

- System architecture or boundaries
- Storage model decisions
- Code conventions or standards
- Feature scope

## Before Moving to the Next Unit

1. The current story works end to end within its defined acceptance
   criteria.
2. No invariant defined in `architecture.md` was violated.
3. `progress-tracker.md` reflects the completed work.
4. The project's build/test command passes [fill in once tooling is chosen].
