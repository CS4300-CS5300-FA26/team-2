# Agent Rules — Pathfinder

Scope: this file and everything under `docs/agents/` only. It applies to any AI coding agent (Claude Code, Codex, Cursor, etc.) working within this directory tree. Do not copy, summarize, or move these rules to the repo root or any other directory — they stay scoped here.

## Reading order

Before implementing or making any architectural decision, read:

1. `context/project-overview.md` — product definition, goals, features, and scope
2. `context/architecture.md` — system structure, boundaries, storage model, and invariants
3. `context/ui-context.md` — theme, colors, typography, and component conventions
4. `context/code-standards.md` — implementation rules and conventions
5. `context/ai-workflow-rules.md` — development workflow, scoping rules, and delivery approach
6. `context/progress-tracker.md` — current phase, completed work, open questions, and next steps

Update `context/progress-tracker.md` after each meaningful implementation change.

If implementation changes the architecture, scope, or standards documented in the context files, update the relevant file before continuing.

## Repo-level pointers (not duplicated here)

- Branch model, PR expectations, commit style: `/CONTRIBUTING.md`
- AI-assisted commit trailer format: `/docs/ai-authorship.md`
- Branch naming: `/docs/branch-naming.md`
