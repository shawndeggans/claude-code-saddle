# Project: [PROJECT_NAME]

## Overview

[One paragraph describing what this project does, its main purpose, and target users]

## Key Paths

| Path | Purpose |
|------|---------|
| `src/main.py` | Application entry point |
| `src/api/` | REST API routes |
| `src/models/` | Database models |
| `src/services/` | Business logic |
| `config/` | Configuration files |
| `tests/` | Test suite |

## Tech Stack

- **Language**: Python 3.9+
- **Framework**: [FastAPI/Django/Flask]
- **Database**: [PostgreSQL/SQLite/MongoDB]
- **Testing**: pytest
- **Linting**: ruff

## Critical Rules (Project-Specific)

Add rules that differ from or extend saddle defaults:

- [Example: ALWAYS use async/await for database operations]
- [Example: NEVER import from src.legacy module - it's deprecated]

## Common Commands

```bash
# Run tests
pytest project/tests/ -v

# Start development server
python project/src/main.py

# Run migrations
alembic upgrade head

# Run linting
ruff check project/

# Format code
ruff format project/
```

## Architecture Notes

### Data Flow
[Describe how data flows through the application]

### Key Patterns
- [Pattern 1: e.g., Repository pattern for database access]
- [Pattern 2: e.g., Dependency injection via FastAPI Depends]

### External Dependencies
- [Service 1: What it does, how to access]
- [Service 2: What it does, how to access]

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT signing key | (required) |
| `DEBUG` | Enable debug mode | `false` |

## Known Issues / Tech Debt

Track known issues and planned improvements:

- [ ] [Issue 1: Description and potential fix]
- [ ] [Issue 2: Description and potential fix]

## Recent Changes

Brief log of recent significant changes:

- [Date]: [Description of change]
