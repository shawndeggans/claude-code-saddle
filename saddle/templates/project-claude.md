# Project: [PROJECT_NAME]

## Overview

[One paragraph describing what this project does, its main purpose, and target users]

## Enforcement

Configure optional enforcement features:

```
TDD: disabled
```

Set `TDD: enabled` to activate TDD Guard advisory checks.

## Key Paths

| Path | Purpose |
|------|---------|
| `src/main.py` | Application entry point |
| `src/api/` | REST API routes |
| `src/models/` | Database models |
| `src/services/` | Business logic |
| `tests/` | Test suite |

## Tech Stack

- **Language**: Python 3.9+
- **Framework**: [FastAPI/Django/Flask]
- **Database**: [PostgreSQL/SQLite/MongoDB]
- **Testing**: pytest
- **Linting**: ruff

## Project-Specific Rules

Add rules that differ from or extend saddle defaults:

- [Example: ALWAYS use async/await for database operations]
- [Example: NEVER import from src.legacy module - deprecated]

## Common Commands

```bash
# Run tests
pytest project/tests/ -v

# Start development server
python project/src/main.py

# Run linting
ruff check project/
```

## Architecture Notes

### Key Patterns
- [Pattern 1: e.g., Repository pattern for database access]
- [Pattern 2: e.g., Dependency injection via FastAPI Depends]

### External Dependencies
- [Service 1: What it does, how to access]

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT signing key | (required) |

## Known Issues / Tech Debt

- [ ] [Issue 1: Description and potential fix]
