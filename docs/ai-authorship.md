# AI authorship in commits

Disclose AI assistance in the commit itself, not just the shared AI-usage doc. Goes as trailers **after** the human-written subject and body; the message still has to explain what changed and why on its own.

## Format

```
<subject line>

<body — what changed, why, same as any other commit>

AI-Assisted: yes
AI-Tool: <tool, e.g. Claude (claude-code), Copilot, ChatGPT>
AI-Scope: <what it did — e.g. "generated test stubs, I reviewed and edited">
```

No `Co-Authored-By` trailer, the `AI-*` trailers above are the record of AI involvement, don't duplicate it as co-authorship.

No AI involved: omit the `AI-*` trailers entirely. Don't write `AI-Assisted: no`.

## Rules

- `AI-Scope` describes what the *AI* did, not what the commit does — that's the body's job. One line.
- Trailers are git-trailer format (`Key: value`, no blank line between them), so they're parseable with `git log --format=%(trailers)`.
- Applies to any commit where AI materially contributed to the content (code, tests, docs, config) — not spell-check or autocomplete-level assistance.
- Reviewer checks `AI-Scope` claims match the diff, same as any other commit claim.
