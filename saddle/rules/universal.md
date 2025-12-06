# Universal Rules

These rules apply to every session, regardless of project type. They are designed to prevent common failure modes in AI-assisted development.

## Format Standards

### No Emojis
- Do not use emojis in code, comments, commit messages, or documentation
- Rationale: Emojis cause encoding issues, accessibility problems, and inconsistent rendering across terminals

### Naming Conventions
- Use `snake_case` for Python files, functions, and variables
- Use `PascalCase` for Python classes
- Use `kebab-case` for shell scripts and markdown files
- Be consistent with existing project conventions

### Code Style
- Follow the project's existing style (check for `.editorconfig`, `pyproject.toml`, etc.)
- Run linters before committing: `ruff check` for Python
- Keep lines under 88 characters (ruff default)

## Session Management

### Before Starting Work
1. Read `saddle/index/CODEBASE.md` to understand current codebase state
2. Check `saddle/templates/todo.md` for any in-progress work
3. Review recent commits: `git log --oneline -10`

### During Work
1. Update `todo.md` as tasks progress
2. Commit frequently with clear messages
3. Run tests after each significant change

### After Completing Work
1. Update `todo.md` with completed items
2. Ensure all tests pass
3. Update documentation if behavior changed

## Context Preservation

### Why External State Matters
- Conversation context is lost between sessions
- File-based state (todo.md, indexes) persists
- Always write important context to files, not just conversation

### What to Persist
- Current task and progress in `todo.md`
- Decisions and rationale in code comments
- Architecture choices in `project/CLAUDE.md`

## Error Handling

### When Blocked
1. Read the blocking message carefully
2. Follow the suggested remediation
3. If unclear, check the relevant rule file in `saddle/rules/`

### When Uncertain
1. Ask for clarification rather than guessing
2. Check existing code patterns before implementing new ones
3. Prefer simple solutions over clever ones
