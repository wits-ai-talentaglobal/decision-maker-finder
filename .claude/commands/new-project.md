 # New Project Setup

Initialize this repository for Claude Code.

## Instructions

First inspect the current directory and identify:

- The programming language.
- Frameworks and libraries.
- Package manager.
- Application entry points.
- Source directories.
- Test directories.
- Formatter, linter, and type checker.
- Build and development commands.
- Deployment configuration.
- Existing documentation.
- Existing environment or configuration files.

Do not expose or print secret values. Read only the names and structure of sensitive files when necessary.

Then create or update the following:

### 1. Root `CLAUDE.md`

Create a concise project-specific `CLAUDE.md` containing:

- Project purpose.
- Technology stack.
- Important directory structure.
- Development commands.
- Test commands.
- Formatting and linting commands.
- Build commands.
- Architecture notes.
- Important coding conventions.
- Database or API conventions, if applicable.
- Security requirements.
- Definition of done.

Do not copy generic global instructions into this file.

### 2. `.gitignore`

Ensure the project ignores appropriate sensitive and generated files, including:

- `.env`
- `.env.*`
- `!.env.example`
- Local settings files
- Credentials
- Private keys
- Build output
- Dependency directories
- Caches
- IDE files

Preserve existing `.gitignore` rules.

### 3. `.env.example`

If the project uses environment variables, create or update `.env.example`.

Include variable names and safe placeholders only. Never include real credentials.

### 4. `.claude/`

Create `.claude/` only if the project benefits from project-specific configuration.

Possible files:

- `.claude/settings.json` for shared, non-secret settings.
- `.claude/settings.local.json` for personal settings that must not be committed.
- `.claude/rules/` for modular project rules.
- `.claude/skills/` for reusable project workflows.

Do not put real API keys, passwords, tokens, or private keys in any committed file.

### 5. Validation

Run only commands discovered from the project configuration.

At minimum, when available:

- Formatter check.
- Linter.
- Type checker.
- Relevant tests.
- Build or compilation check.

Do not install dependencies or modify external systems without asking first.

## Final response

Report:

- Detected stack.
- Files created or updated.
- Commands run.
- Validation results.
- Any assumptions.
- Any actions requiring user approval.