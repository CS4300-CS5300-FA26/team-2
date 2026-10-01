# Branch naming

Story branches: `feat/<slice>/us<id>-<short-slug>`

Slices: `signup-user-management`, `file-upload-digitization`, `ai-intelligence`, `bookmarking-search`, `progress-tracking-alerts` — match the long-lived branch names.

Examples:
- `feat/signup-user-management/us1.1-password`
- `feat/ai-intelligence/us3.2-match-alerts`
- `fix/bookmarking-search/us4.5-status-filter-bug`

Use `fix/` instead of `feat/` for bug fixes. Branch off the relevant slice branch, PR back into it.
