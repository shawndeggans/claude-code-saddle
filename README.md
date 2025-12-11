# Claude Code Saddle

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**A lightweight control layer for AI-assisted development.** Provides advisory guardrails that inform without blocking, trusting developer judgment.

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/claude-code-saddle.git
cd claude-code-saddle
./scripts/setup.sh
source .venv/bin/activate

# Add your code to project/, then commit
# Codebase index updates automatically on each commit
```

---

## What It Does

| Feature | Behavior |
|---------|----------|
| **Codebase Index** | Auto-generates on commit. Query `saddle/index/CODEBASE.md` for structure. |
| **Automatic Behaviors** | Claude self-manages: index checks, test runs, planning, cleanup suggestions. |
| **TDD Advisory** | Opt-in per project. Warns (never blocks) when test files are missing. |
| **Doc Verification** | Advises on missing docstrings and CHANGELOG entries. |
| **Dead Code Detection** | Finds unused code and stale files via `/cleanup` command. |
| **Expert Systems** | Domain-specific MCP servers with embedded LLMs. Delegate specialized work via consult, execute, review, troubleshoot tools. |

**Advisory philosophy**: Hooks provide guidance but trust developer judgment. No hard blocks. Claude handles operational tasks automatically so humans focus on decisions.

---

## Project Structure

```
claude-code-saddle/
  CLAUDE.md                 # Universal guidelines
  project/                  # Your code goes here
    CLAUDE.md             # Project-specific rules (create from template)
    src/
    tests/
  saddle/
    experts/              # Expert systems (MCP servers with domain knowledge)
    index/                # Auto-generated codebase map
    workflows/            # TDD Guard, doc-verify (advisory)
    cleanup/              # Dead code and archive tools
    templates/            # Project CLAUDE.md template, assessment template
  scripts/
    setup.sh              # One-command setup
  .claude/
    hooks/                # Session start, pre/post tool use (advisory)
```

---

## Configuration

### Enable TDD Advisory (Per Project)

TDD is **disabled by default**. To enable, add to `project/CLAUDE.md`:

```markdown
## Enforcement
TDD: enabled
```

When enabled, the TDD Guard hook will output advisories when test files are missing.

### Project-Specific Rules

Copy `saddle/templates/project-claude.md` to `project/CLAUDE.md` and customize:

```bash
cp saddle/templates/project-claude.md project/CLAUDE.md
```

Add project-specific paths, commands, and guidelines.

---

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
| `/diff [ref]` | Summarize changes since ref |

---

## Components

### Index Generator

Auto-generates on each commit via post-commit hook. Manual regeneration:

```bash
python saddle/index/generator/index_generator.py --full
```

**Generated files:**
- `codebase-index.json` - Functions, classes, imports per file
- `dependency-graph.json` - Module import relationships
- `CODEBASE.md` - Human-readable summary

### TDD Guard (Advisory)

Checks for test files when writing implementation code.

```bash
# Manual check
python saddle/workflows/tdd-guard/tdd_guard.py src/auth.py write --json
```

**Exit codes:** Always advisory (exit 0). Outputs guidance when tests missing.

### Doc Verify (Advisory)

Checks docstrings and CHANGELOG entries.

```bash
python saddle/workflows/doc-verify/doc_verify.py --files src/module.py
```

### Cleanup Tools

```bash
# Find dead code
python saddle/cleanup/dead_code_detector.py project/ --format markdown

# Find stale files
python saddle/cleanup/stale_file_tracker.py project/ --threshold 180

# Archive unused code
python saddle/cleanup/archive_manager.py archive src/old.py --reason "deprecated"
```

### Expert Systems

Domain-specific MCP servers with embedded LLMs for specialized guidance.

```bash
# Create an expert
./scripts/init-expert.sh databricks "Databricks platform and Asset Bundles"

# Test and start
./scripts/test-expert.sh databricks
./scripts/start-expert.sh databricks
```

**Available tools** (per expert): `consult`, `execute`, `review`, `troubleshoot`

See `saddle/experts/README.md` for full documentation.

---

## Hooks

All hooks are **advisory only** - they inform but never block operations.

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` | Session start | Shows index location and git status |
| `pre-tool-use.sh` | Before Write/Edit | TDD advisory (when enabled) |
| `post-tool-use.sh` | After Write/Edit | Documentation advisory |

---

## Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:

- **Ruff**: Linting and formatting
- **Vulture**: Dead code detection
- **Bandit**: Security scanning
- **Index update**: Auto-regenerates codebase index (post-commit)

---

## Dependencies

| Package | Purpose |
|---------|---------|
| tree-sitter-languages | Multi-language code parsing |
| vulture | Dead code detection |
| gitpython | Git history analysis |
| ruff | Linting and formatting |
| pre-commit | Git hook management |

---

## Philosophy

### Advisory Over Blocking

The saddle trusts developer judgment. Hooks output guidance when they detect issues, but they never prevent operations. You decide whether to act on the advice.

### Auto-Generated Context

The codebase index updates automatically on each commit. No manual regeneration needed. Query `saddle/index/CODEBASE.md` to understand code structure.

### Minimal Configuration

- One `CLAUDE.md` file for universal guidelines
- One `project/CLAUDE.md` for project-specific rules
- TDD is opt-in, not forced
- No required session state files

---

## Contributing

```bash
git clone https://github.com/yourusername/claude-code-saddle.git
cd claude-code-saddle
./scripts/setup.sh
source .venv/bin/activate

# Run tests
pytest project/tests/

# Lint
ruff check saddle/
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built for use with [Claude Code](https://claude.ai/), Anthropic's CLI for Claude.
