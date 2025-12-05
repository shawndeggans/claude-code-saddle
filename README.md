# claude-code-saddle

Wraps codebases with AI tooling.

## Installation

```bash
pip install -e ".[dev]"
pre-commit install
```

## Project Structure

- `saddle/` - Main package
  - `rules/` - Rule definitions
  - `workflows/` - Workflow definitions
    - `tdd-guard/` - TDD guard workflow
    - `doc-verify/` - Documentation verification workflow
  - `index/generator/` - Index generation
  - `cleanup/` - Cleanup utilities
  - `templates/` - Templates
- `project/` - Project files
- `scripts/` - Utility scripts
- `.claude/hooks/` - Claude hooks