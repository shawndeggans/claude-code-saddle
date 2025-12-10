# Claude Code Saddle

A lightweight control layer for AI-assisted development.

## Quick Reference

- **Your code**: `project/`
- **Codebase map**: `saddle/index/CODEBASE.md` (auto-generated on commit)
- **Project rules**: `project/CLAUDE.md`

## Guidelines

### Code Quality

- **Run tests before committing**: `pytest project/tests/`
  *Rationale: Catches regressions before they reach main branch*

- **Run linting before committing**: `ruff check project/`
  *Rationale: Consistent style reduces cognitive load in reviews*

- **No secrets in code** (check for .env, credentials, API keys)
  *Rationale: Secrets in git history are nearly impossible to fully remove*

- **No emojis** in code, comments, or commit messages
  *Rationale: Keeps output clean and professional across all terminals*

### Working Style

- **Check `saddle/index/CODEBASE.md`** before asking where things are
  *Rationale: The index is authoritative and auto-updated; saves exploration time*

- **Read existing code** before proposing changes
  *Rationale: Understanding context prevents accidental breakage and maintains consistency*

- **Prefer simple solutions** over clever ones
  *Rationale: Code is read more often than written; clarity wins*

### Infrastructure

- **Infrastructure changes go through IaC**, not direct CLI commands
  *Rationale: IaC provides audit trail, rollback capability, and reproducibility*

### Testing (Optional - Enable Per Project)

TDD enforcement is **disabled by default**. To enable TDD Guard for a project, add to `project/CLAUDE.md`:

```markdown
## Enforcement
TDD: enabled
```

When enabled, the TDD Guard hook will advise (not block) when test files are missing.

## Commands

| Command | Description |
|---------|-------------|
| `/assess <task>` | Create planning document for complex tasks |
| `/cleanup` | Find dead code and stale files |
| `/index` | Force-regenerate codebase index |
| `/status` | Quick project health check |
| `/context` | Dump context for session resume |
| `/archive <path>` | Move file to archive with metadata |
| `/restore <path>` | Recover file from archive |
| `/diff [ref]` | Summarize changes since ref (default: HEAD) |

### Command Details

**Planning**: `/assess <task>` creates `project/assessments/<date>-<task>.md` from template. Optional, no enforcement.

**Maintenance**: `/cleanup` and `/index` help keep the codebase healthy. Index auto-updates on commit, but `/index` forces immediate refresh.

**Context**: `/status` and `/context` answer "where am I?" - useful after breaks or in new sessions.

**Archiving**: `/archive` moves files to `.archive/` with metadata. `/restore` brings them back. Non-destructive code removal.

## Project Structure

```
claude-code-saddle/
  CLAUDE.md                 # This file - universal guidelines
  project/                  # Your code goes here
    CLAUDE.md             # Project-specific rules
    src/                  # Source code
    tests/                # Test files
  saddle/
    workflows/            # Advisory systems (TDD Guard, doc-verify)
    index/                # Auto-generated codebase indexes
    cleanup/              # Dead code and staleness detection
    templates/            # Assessment template
  scripts/                  # Setup and utility scripts
  .claude/                  # Claude Code hook configurations
```

## Advisory Hooks

The saddle uses **advisory hooks** that inform rather than block:

- **Pre-tool-use**: Checks for test files (when TDD enabled), outputs guidance
- **Post-tool-use**: Checks documentation, logs to session audit trail
- **Session start**: Shows git status and index location

Hooks provide guidance but trust developer judgment. If a hook raises a concern, it will explain why - you decide whether to act on it.

## Project-Specific Rules

See `project/CLAUDE.md` for rules specific to this codebase. Projects can:
- Enable TDD enforcement
- Add custom guidelines
- Override defaults where appropriate
