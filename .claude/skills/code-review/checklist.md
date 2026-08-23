# Code Review Checklist

## Correctness
- [ ] Does the code do what the commit/PR description claims?
- [ ] Are edge cases handled (empty input, null/undefined, zero, negative numbers, concurrency)?
- [ ] Are there off-by-one errors in loops, slices, or pagination?
- [ ] Do error paths actually get exercised, or would an exception here be silently swallowed?

## Security
- [ ] Is any external input (user, API, file) used unsanitized in a query, command, or template?
- [ ] Are secrets, tokens, or credentials hard-coded or logged anywhere?
- [ ] Is authorization checked, not just authentication (can user A access user B's data)?
- [ ] Are new dependencies from a trusted source and reasonably maintained?

## Maintainability
- [ ] Is the change minimal and focused, or does it drift into unrelated refactoring?
- [ ] Are names accurate and consistent with the rest of the codebase?
- [ ] Is there duplicated logic that should reuse an existing function?
- [ ] Would a future reader understand *why*, not just *what*, for any non-obvious code?

## Tests
- [ ] Is new/changed behavior covered by a test?
- [ ] Do the tests actually fail if the change is reverted (not tautological)?

## Docs
- [ ] Does this change require updating README, CLAUDE.md, or API docs?
