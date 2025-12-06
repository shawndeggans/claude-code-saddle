# Claude Code Saddle

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**A control layer for consistent AI-assisted development.** Like a saddle on a horse, it sits on top of your codebase and provides the interface for reliable, enforceable coding practices.

---

## The Problem

After extended sessions with AI coding agents, three failure modes emerge consistently:

1. **Context drift**: The agent gradually forgets rules specified earlier as conversation length increases
2. **CLAUDE.md bloat**: Project-specific instructions accumulate until the file exceeds practical context limits
3. **Enforcement decay**: Workflow requirements (TDD, documentation) are followed initially but abandoned under pressure

## The Solution

Claude Code Saddle addresses these failures through **mechanical enforcement** and **separation of concerns**:

| Layer | Location | Purpose | Update Frequency |
|-------|----------|---------|------------------|
| **Universal Rules** | `CLAUDE.md` | Policies that apply everywhere | Rarely |
| **Workflow Hooks** | `.claude/hooks/` | Mechanical enforcement (TDD, docs) | Per-methodology |
| **Project Context** | `project/CLAUDE.md` | Client-specific patterns, APIs | Per-project |
| **Dynamic Index** | `saddle/index/` | Auto-generated codebase map | Per-commit |

**Why this works**: Hooks block non-compliant actions mechanically - they don't rely on the AI remembering to follow rules. External state (indexes, todo files) persists across sessions while conversation context does not.

---

## Features

### TDD Guard
Mechanical enforcement of test-driven development. Blocks code writes without corresponding test files.

```
User: "Write the authentication module"
Claude: [Attempts to write src/auth.py]
  ↓
PreToolUse Hook fires
  ↓
TDD Guard checks: Does tests/test_auth.py exist?
  ↓
NO → Operation BLOCKED with guidance
  ↓
Claude: "I need to write the tests first..."
```

### Auto-Indexing
Generates searchable structural maps of your codebase:
- `codebase-index.json` - File/function/class map
- `dependency-graph.json` - Import relationships
- `stale-files.json` - Archival candidates
- `CODEBASE.md` - Human-readable summary

### Documentation Verification
Pre-commit checks ensuring documentation accompanies code changes:
- Module docstrings required for new files
- Function docstrings for public APIs
- CHANGELOG updates for feature additions

### Dead Code Detection
Combines vulture and deadcode tools with intelligent deduplication:
- Confidence-based prioritization
- Safe auto-fix mode (dry-run default)
- Multiple output formats (text, JSON, markdown)

### Archive System
Non-destructive code removal with full restoration capability:
- Moves files to `.archive/` with metadata
- Tracks original paths, dates, and reasons
- Easy restoration when needed

### Session Persistence
External state files that survive across AI sessions:
- `todo.md` - Current task tracking
- `assessment.md` - Pre-coding analysis for large changes
- Generated indexes refresh context automatically

---

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-code-saddle.git
cd claude-code-saddle

# Run setup script
./scripts/setup.sh

# Activate virtual environment
source .venv/bin/activate
```

### Add Your Project

**Option A: Git Submodule** (for external repositories)
```bash
./scripts/init-submodule.sh git@github.com:org/repo.git main
```

**Option B: Nested Folder** (for local code)
```bash
./scripts/init-nested.sh /path/to/your/code
# Or create empty structure:
./scripts/init-nested.sh
```

### Generate Index
```bash
./scripts/generate-index.sh --full
```

---

## Installation (Detailed)

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks
```bash
pre-commit install
```

### 4. Verify Installation
```bash
# Test TDD Guard
python saddle/workflows/tdd-guard/tdd_guard.py --help

# Test Index Generator
python saddle/index/generator/index_generator.py --help

# Run linting
ruff check saddle/
```

---

## Usage

### Scripts

| Script | Description | Example |
|--------|-------------|---------|
| `setup.sh` | Initialize environment | `./scripts/setup.sh` |
| `init-submodule.sh` | Add project as git submodule | `./scripts/init-submodule.sh <url> [branch]` |
| `init-nested.sh` | Copy local code or create empty project | `./scripts/init-nested.sh [path]` |
| `generate-index.sh` | Regenerate codebase index | `./scripts/generate-index.sh --full` |
| `run-cleanup.sh` | Run dead code/stale file analysis | `./scripts/run-cleanup.sh --report` |

### Command Shortcuts (for Claude Code)

| Command | Action |
|---------|--------|
| `/index` | Regenerate codebase index |
| `/cleanup` | Run dead code and stale file detection |
| `/assess <task>` | Create pre-coding assessment document |
| `/todo` | Show current session state |

### Common Workflows

**Start a new coding session:**
```bash
# Check current state
cat saddle/templates/todo.md
cat saddle/index/CODEBASE.md | head -50
```

**After making changes:**
```bash
# Regenerate index
./scripts/generate-index.sh --incremental

# Check for issues
./scripts/run-cleanup.sh --report
```

**Archive unused code:**
```bash
python saddle/cleanup/archive_manager.py archive src/old_module.py --reason "deprecated"
python saddle/cleanup/archive_manager.py list
```

---

## Project Structure

```
claude-code-saddle/
├── CLAUDE.md                    # Universal rules (loaded every session)
├── README.md                    # This file
├── SETUP.md                     # Detailed setup guide with prompts
├── pyproject.toml               # Python project configuration
├── .pre-commit-config.yaml      # Pre-commit hook configuration
│
├── .claude/
│   ├── settings.json            # Claude Code hook configuration
│   └── hooks/
│       ├── pre-tool-use.sh      # TDD enforcement hook
│       ├── post-tool-use.sh     # Documentation verification
│       └── session-start.sh     # Context refresh on new sessions
│
├── saddle/                      # Main package (~4,000 LOC)
│   ├── index/
│   │   └── generator/
│   │       ├── index_generator.py    # Main indexing orchestrator
│   │       ├── parsers/
│   │       │   ├── python_parser.py  # Python AST parsing
│   │       │   ├── js_parser.py      # JavaScript/TypeScript parsing
│   │       │   └── generic_parser.py # Fallback for other languages
│   │       └── embeddings/
│   │           └── embed_code.py     # Optional semantic search
│   │
│   ├── workflows/
│   │   ├── tdd-guard/
│   │   │   ├── tdd_guard.py     # TDD enforcement logic
│   │   │   ├── config.yaml      # Test pattern configuration
│   │   │   └── README.md        # TDD Guard documentation
│   │   └── doc-verify/
│   │       ├── doc_verify.py    # Documentation checker
│   │       └── templates/       # Docstring templates
│   │
│   ├── cleanup/
│   │   ├── dead_code_detector.py   # Vulture + deadcode wrapper
│   │   ├── stale_file_tracker.py   # Git-based staleness detection
│   │   └── archive_manager.py      # Non-destructive archival
│   │
│   ├── rules/                   # Modular rule documentation
│   │   ├── universal.md         # Core rules with rationale
│   │   ├── testing-required.md  # TDD methodology
│   │   ├── documentation.md     # Doc standards
│   │   └── no-direct-deploy.md  # IaC-only policy
│   │
│   └── templates/               # Session management templates
│       ├── todo.md              # Current session state
│       ├── assessment.md        # Pre-coding analysis template
│       └── project-claude.md    # Project CLAUDE.md template
│
├── project/                     # Your code goes here
│   ├── CLAUDE.md               # Project-specific rules
│   ├── src/
│   └── tests/
│
└── scripts/                     # Utility scripts
    ├── setup.sh
    ├── init-submodule.sh
    ├── init-nested.sh
    ├── generate-index.sh
    └── run-cleanup.sh
```

---

## Components

### Index Generator

Parses your codebase and generates structural indexes for quick querying.

**Supported Languages:**
- Python (AST-based, full support)
- JavaScript/TypeScript (tree-sitter, good support)
- Go, Rust, Ruby, Java, C/C++ (generic parser, basic support)

**Generated Files:**

| File | Contents |
|------|----------|
| `codebase-index.json` | Functions, classes, imports per file |
| `dependency-graph.json` | Module import relationships |
| `stale-files.json` | Files not modified/referenced recently |
| `CODEBASE.md` | Human-readable summary with statistics |

**Usage:**
```bash
# Full rebuild
python saddle/index/generator/index_generator.py --full --verbose

# Incremental update (only changed files)
python saddle/index/generator/index_generator.py --incremental
```

### TDD Guard

Enforces test-driven development by intercepting file operations.

**How it works:**
1. PreToolUse hook fires before Write/Edit operations
2. TDD Guard checks if corresponding test file exists
3. Returns: ALLOW (0), BLOCK (1), or WARN (2)

**Configuration** (`saddle/workflows/tdd-guard/config.yaml`):
```yaml
test_patterns:
  "src/**/*.py": "tests/**/test_*.py"
  "src/**/*.js": "tests/**/*.test.js"

excluded_paths:
  - "**/migrations/**"
  - "**/__init__.py"
  - "**/conftest.py"

strict_mode: false  # Set true to block on warnings
```

**CLI Usage:**
```bash
# Check a file
python saddle/workflows/tdd-guard/tdd_guard.py src/auth.py write

# With JSON output
python saddle/workflows/tdd-guard/tdd_guard.py src/auth.py edit --json

# Strict mode
python saddle/workflows/tdd-guard/tdd_guard.py src/auth.py write --strict
```

### Doc Verify

Ensures documentation accompanies code changes.

**Checks performed:**
- Module-level docstrings
- Public function docstrings
- Public class docstrings
- CHANGELOG updates for API changes

**Usage:**
```bash
# Check staged files
python saddle/workflows/doc-verify/doc_verify.py --check-staged

# Check specific file
python saddle/workflows/doc-verify/doc_verify.py --files src/module.py

# Strict mode (warnings become errors)
python saddle/workflows/doc-verify/doc_verify.py --check-staged --strict
```

### Cleanup System

Three tools for maintaining code hygiene:

**Dead Code Detector:**
```bash
# Report dead code
python saddle/cleanup/dead_code_detector.py project/ --format markdown

# Show what would be removed
python saddle/cleanup/dead_code_detector.py project/ --dry-run
```

**Stale File Tracker:**
```bash
# Find files not modified in 180+ days
python saddle/cleanup/stale_file_tracker.py project/ --threshold 180
```

**Archive Manager:**
```bash
# Archive a file
python saddle/cleanup/archive_manager.py archive src/old.py --reason "deprecated"

# List archived files
python saddle/cleanup/archive_manager.py list

# Restore a file
python saddle/cleanup/archive_manager.py restore src/old.py

# Purge old archives
python saddle/cleanup/archive_manager.py purge --older-than 1y --dry-run
```

---

## Configuration

### CLAUDE.md

The root `CLAUDE.md` defines universal rules. Key sections:

```markdown
## Universal Rules

### NEVER
- Use emojis in code, comments, or commits
- Deploy directly (IaC only)
- Commit without running tests
- Skip assessment for changes >50 LOC

### ALWAYS
- Update todo.md before/after tasks
- Run test suite before committing
- Check CODEBASE.md before asking about code locations
- Write tests BEFORE implementation
```

### Project-Specific Rules

Create `project/CLAUDE.md` for project-specific context:
- Entry points and key paths
- Common commands
- Architecture notes
- Known issues

### Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:
- **Ruff**: Linting and formatting
- **Vulture**: Dead code detection
- **Bandit**: Security scanning

### Claude Code Integration

Hooks are configured in `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command", "command": "bash .claude/hooks/pre-tool-use.sh"}]
      }
    ]
  }
}
```

---

## For Claude Code Users

### How Enforcement Works

1. **Session Start**: The session-start hook outputs key rules and current context
2. **Before Writing**: PreToolUse hook runs TDD Guard to verify tests exist
3. **After Writing**: PostToolUse hook runs doc-verify to check documentation
4. **Commit Time**: Pre-commit hooks run ruff, vulture, and bandit

### Customizing Rules

**Disable TDD Guard for a project:**
```yaml
# project/.tdd-guard.yaml
strict_mode: false
excluded_paths:
  - "**/*"  # Disable for all files
```

**Add project-specific rules:**
Edit `project/CLAUDE.md` with rules that extend or override saddle defaults.

### Session State

The saddle maintains state across sessions via files:
- `saddle/templates/todo.md` - Track current work
- `saddle/index/CODEBASE.md` - Codebase overview (auto-generated)
- `saddle/templates/assessment.md` - Pre-coding analysis template

---

## Dependencies

### Core
| Package | Purpose |
|---------|---------|
| tree-sitter-languages | Multi-language code parsing |
| vulture | Dead code detection |
| deadcode | Additional dead code detection |
| gitpython | Git history analysis |
| pyyaml | Configuration parsing |

### Optional
| Package | Purpose |
|---------|---------|
| chromadb | Vector database for semantic search |
| sentence-transformers | Code embeddings |

### Development
| Package | Purpose |
|---------|---------|
| ruff | Linting and formatting |
| bandit | Security scanning |
| pre-commit | Git hook management |
| pytest | Testing |

---

## Contributing

### Development Setup
```bash
git clone https://github.com/yourusername/claude-code-saddle.git
cd claude-code-saddle
./scripts/setup.sh
source .venv/bin/activate
```

### Running Tests
```bash
pytest tests/
```

### Code Style
This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:
```bash
ruff check saddle/      # Lint
ruff format saddle/     # Format
```

### Pre-commit
All commits are checked by pre-commit hooks. Install with:
```bash
pre-commit install
```

---

## Philosophy

### Mechanical Enforcement Over Instructions

Rules that say "please do X" are easily forgotten. Hooks that block non-compliant actions are not. The saddle prioritizes mechanical enforcement:

- **TDD Guard blocks** writing implementation without tests
- **Pre-commit hooks block** commits with linting errors
- **Doc-verify warns** about missing documentation

### External State Over Context Memory

AI conversation context is lost between sessions. File-based state persists:

- `todo.md` tracks current work
- Generated indexes provide codebase context
- Archives preserve removed code with metadata

### Thin Project CLAUDE.md

Keep project-specific rules minimal. The saddle handles universal enforcement; the project CLAUDE.md should only contain what differs from defaults.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built for use with [Claude Code](https://claude.ai/), Anthropic's CLI for Claude.
