---
description: Deploy the project to the given environment
argument-hint: [environment]
---

<!--
  NOTE: commands/ is the legacy single-file mechanism for slash commands.
  New invokable capabilities should generally be added as skills under
  .claude/skills/ instead (see .claude/skills/code-review/ for an example) —
  skills support supporting files, richer descriptions for auto-invocation,
  and are the currently recommended approach. This file is kept as a
  reference example of the legacy format.
-->

# Deploy

Deploy the project to the **$ARGUMENTS** environment (e.g. `staging`, `production`).

## Steps

1. Confirm the target environment was provided; if not, ask which one.
2. Run the project's test suite and fail fast if it doesn't pass.
3. Run the build/lint checks defined in the project's `CLAUDE.md` under "Common Commands".
4. Confirm with the user before deploying to `production` specifically.
5. Run the actual deploy command for this project (fill in once the deployment
   target/tooling is chosen — e.g. `flyctl deploy`, `vercel --prod`, `kubectl apply -f ...`).
6. Report what was deployed, to where, and a link to logs/dashboard if available.
