# Code Style

General coding rules that apply across the whole project (no path scoping).

- Prefer clarity over cleverness: a longer, obvious implementation beats a short, opaque one.
- Keep functions focused on one responsibility; extract when a function does two distinct things.
- Name things for what they are, not how they're implemented (`retryCount`, not `i2`).
- Avoid deep nesting — prefer early returns / guard clauses over nested conditionals.
- Don't leave commented-out code, `console.log`/debug prints, or TODO markers without an owner.
- New dependencies must be justified — prefer the standard library or an existing dependency first.
- Keep diffs minimal: don't reformat or reorganize code you weren't asked to touch.
