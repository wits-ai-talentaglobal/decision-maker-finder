---
paths:
  - "**/*.test.*"
  - "**/*.spec.*"
  - "**/__tests__/**"
  - "test/**"
  - "tests/**"
---

# Testing Conventions

- Every new behavior change needs a corresponding test — don't leave changed logic untested.
- Test names describe the behavior under test and the expected outcome, not the implementation.
- Prefer one assertion focus per test; split unrelated assertions into separate tests.
- Mock only true external boundaries (network, filesystem, third-party APIs) — don't mock
  internal collaborators just to isolate a unit.
- Keep fixtures/setup minimal and local to the test file unless genuinely shared.
- A failing test must fail for the reason its name claims — verify red before green.
