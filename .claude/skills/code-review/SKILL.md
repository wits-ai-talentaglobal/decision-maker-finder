---
name: code-review
description: Review code changes (a diff, a file, or a PR) against this project's checklist for correctness, security, and maintainability issues before merging. Use when asked to review, check, or audit code changes.
argument-hint: "[file-or-diff-target]"
---

# Code Review

Review the target ($ARGUMENTS, or the current uncommitted diff if no argument is given)
against `.claude/skills/code-review/checklist.md`.

## Process

1. Determine the review target:
   - No argument → `git diff` (staged + unstaged) plus untracked new files.
   - A file path → review that file in full.
   - A PR number / branch name → diff against the base branch.
2. Read the target and the checklist in `checklist.md`.
3. Walk the checklist section by section; only report items that actually apply to this diff.
4. For each finding, cite the file and line, state the concrete failure scenario (not just
   "this could be an issue"), and suggest a fix.
5. Do not rewrite the code yourself unless explicitly asked — report findings first.

## Output

Group findings by severity (Blocking / Should Fix / Nit). If nothing of substance is found,
say so plainly rather than inventing minor nitpicks to fill space.
