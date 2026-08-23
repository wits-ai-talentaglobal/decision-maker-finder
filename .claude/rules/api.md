---
paths:
  - "src/api/**"
---

# API Rules

- Validate and sanitize all external input at the boundary before it reaches business logic.
- Never trust client-supplied IDs for authorization — always check the requester owns the resource.
- Return consistent error shapes (status code + machine-readable error code + human message).
- Don't leak internal error details (stack traces, SQL, file paths) in API responses.
- New or changed endpoints must update API documentation and any client-facing schema/types.
- Breaking changes to existing endpoints require versioning or an explicit migration plan — never
  silently change response shape or semantics.
