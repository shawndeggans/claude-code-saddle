# Claude Code Saddle - Repository Setup Guide

> **Purpose**: This document provides prompts and instructions for an AI agent to set up a **Saddle** - a standardized wrapper repository that lets you ride any codebase with consistent tooling, rules enforcement, and documentation management. Like a saddle on a horse, it sits on top of your project and gives you control.

## Table of Contents

1. [Philosophy & Design Rationale](#philosophy--design-rationale)
2. [Project Structure](#project-structure)
3. [Setup Prompts](#setup-prompts)
4. [Tool Configurations](#tool-configurations)
5. [CLAUDE.md Architecture](#claudemd-architecture)
6. [Hook System](#hook-system)
7. [Auto-Indexing System](#auto-indexing-system)
8. [Use Cases & Examples](#use-cases--examples)

---

## Philosophy & Design Rationale

### The Core Problem

After extended sessions with AI coding agents, three failure modes emerge consistently:

1. **Context drift**: The agent gradually forgets rules specified in CLAUDE.md as conversation length increases
2. **CLAUDE.md bloat**: Project-specific instructions accumulate until the file exceeds practical context limits
3. **Enforcement decay**: Workflow requirements (TDD, documentation) are followed initially but abandoned under pressure

### The Saddle Solution

This repository template addresses these failures through **separation of concerns** - like a well-fitted saddle that distributes weight properly:

| Layer | Location | Purpose | Update Frequency |
|-------|----------|---------|------------------|
| **Universal Rules** | `/saddle/CLAUDE.md` | Policies that apply everywhere (no emojis, IaC-only, etc.) | Rarely |
| **Workflow Hooks** | `/saddle/hooks/` | Mechanical enforcement (TDD, docs) | Per-methodology |
| **Project Context** | `/project/CLAUDE.md` | Client-specific patterns, APIs, conventions | Per-project |
| **Dynamic Index** | `/saddle/index/` | Auto-generated codebase map | Per-commit |

**Why this works**: Claude Code loads CLAUDE.md files hierarchically. By placing immutable rules in the saddle layer and project-specific context in a nested folder, we keep each file small and focused. The hooks enforce behavior mechanically rather than relying on instruction-following. Think of it as the saddle (universal rules) sitting on the horse (your project) - the saddle provides the interface and control, the horse provides the power.

### Design Principles

1. **Mechanical enforcement over instructions**: Hooks that block actions are more reliable than rules that request compliance
2. **External state over context memory**: Files the agent reads/writes persist across sessions; conversation context does not
3. **Thin project CLAUDE.md**: Project-specific files should contain only what differs from saddle defaults
4. **Queryable codebase**: Treat code as data; generate indexes that answer questions without full file reads

---

## Project Structure

```
claude-code-saddle/
├── CLAUDE.md                      # Saddle-level rules (universal)
├── CLAUDE.local.md                # Personal overrides (gitignored)
├── .claude/
│   ├── settings.json              # Claude Code configuration
│   └── hooks/
│       ├── pre-tool-use.sh        # TDD enforcement hook
│       ├── post-tool-use.sh       # Documentation verification
│       └── session-start.sh       # Context refresh on session start
├── saddle/
│   ├── rules/
│   │   ├── universal.md           # Rules loaded into every session
│   │   ├── no-direct-deploy.md    # IaC-only deployment policy
│   │   ├── testing-required.md    # TDD methodology requirements
│   │   └── documentation.md       # Doc-before-commit policy
│   ├── workflows/
│   │   ├── tdd-guard/             # TDD enforcement system
│   │   │   ├── tdd_guard.py
│   │   │   ├── config.yaml
│   │   │   └── README.md
│   │   ├── doc-verify/            # Documentation verification
│   │   │   ├── doc_verify.py
│   │   │   └── templates/
│   │   └── assess-first/          # Assessment-before-coding workflow
│   │       ├── assessment.py
│   │       └── templates/
│   ├── index/
│   │   ├── generator/             # Auto-indexing tooling
│   │   │   ├── index_generator.py
│   │   │   ├── parsers/
│   │   │   │   ├── python_parser.py
│   │   │   │   ├── js_parser.py
│   │   │   │   └── generic_parser.py
│   │   │   └── embeddings/
│   │   │       └── embed_code.py
│   │   ├── codebase-index.json    # Generated: file/function/class map
│   │   ├── dependency-graph.json  # Generated: import relationships
│   │   ├── stale-files.json       # Generated: candidates for archival
│   │   └── CODEBASE.md            # Generated: human-readable index
│   ├── cleanup/
│   │   ├── dead_code_detector.py  # Vulture/deadcode wrapper
│   │   ├── stale_file_tracker.py  # Git-based staleness detection
│   │   └── archive_manager.py     # Archival workflow automation
│   └── templates/
│       ├── project-claude.md      # Template for project CLAUDE.md
│       ├── todo.md                # External state file template
│       └── assessment.md          # Pre-coding assessment template
├── project/                       # CLIENT CODE GOES HERE
│   ├── CLAUDE.md                  # Project-specific context only
│   ├── src/
│   ├── tests/
│   └── ...
├── scripts/
│   ├── setup.sh                   # Initial saddle setup
│   ├── init-submodule.sh          # Add project as git submodule
│   ├── init-nested.sh             # Copy project into nested folder
│   ├── generate-index.sh          # Trigger index regeneration
│   └── run-cleanup.sh             # Execute cleanup analysis
├── .pre-commit-config.yaml        # Pre-commit hook configuration
├── pyproject.toml                 # Python dependencies
└── README.md                      # Repository documentation
```

### Why This Structure?

**`/saddle/rules/`**: Modular rule files allow selective loading. A client uncomfortable with strict TDD can disable `testing-required.md` without losing other policies. Each rule file is small enough to fit comfortably in context.

**`/saddle/workflows/`**: Self-contained workflow enforcement systems. TDD Guard intercepts file writes; doc-verify checks documentation state; assess-first templates structured thinking. These are mechanical—they don't rely on Claude remembering to follow them.

**`/saddle/index/`**: Auto-generated artifacts that provide codebase queryability. Instead of asking Claude to read 50 files to understand dependencies, it reads `dependency-graph.json`. Instead of searching for "where is authentication handled," it queries vector embeddings or the index.

**`/project/`**: The actual client codebase. Can be a git submodule (linking external repo), a nested folder (code copied in), or a symlink. The saddle doesn't care—it operates on whatever is in this path.

---

## Setup Prompts

Use these prompts with Claude Code to set up the saddle. Run them in sequence.

### Prompt 1: Initialize Saddle Structure

```
Create the claude-code-saddle repository structure. Set up all directories and placeholder files as specified in the project structure. Initialize git, create .gitignore (include CLAUDE.local.md, __pycache__, .env, node_modules, *.pyc, .venv), and create pyproject.toml with these dependencies:

- tree-sitter-languages>=1.10.0
- vulture>=2.10
- deadcode>=2.4.0
- gitpython>=3.1.40
- pyyaml>=6.0
- chromadb>=0.4.0 (for vector embeddings, optional)
- sentence-transformers>=2.2.0 (optional)

Create a README.md explaining the saddle purpose and basic usage.
```

### Prompt 2: Create Universal CLAUDE.md

```
Create the root CLAUDE.md file for the saddle. This file should:

1. Establish identity: "This is a Claude Code Saddle repository - a control layer for consistent AI-assisted development"

2. Define UNIVERSAL rules (prefix each with "ALWAYS:" or "NEVER:"):
   - NEVER use emojis in code, comments, or commit messages
   - NEVER deploy directly to any environment - all infrastructure changes via IaC only
   - NEVER commit without running tests
   - NEVER skip the assessment phase for tasks over 50 lines of code
   - ALWAYS update todo.md before and after each task
   - ALWAYS run the test suite before committing
   - ALWAYS check saddle/index/CODEBASE.md before asking about code location

3. Define workflow triggers:
   - On session start: Read saddle/rules/universal.md and project/CLAUDE.md
   - Before writing code: Check if assessment exists for this task
   - After writing code: Verify tests exist and pass
   - Before commit: Verify documentation is updated

4. Reference the modular rule files in saddle/rules/ for detailed policies

5. Specify the command shortcuts:
   - /index - regenerate codebase index
   - /cleanup - run dead code and stale file detection
   - /assess - create assessment document for current task
   - /todo - show current todo.md state

Keep this file under 150 lines. It should be a navigation hub, not a comprehensive manual.
```

### Prompt 3: Create TDD Guard System

```
Create the TDD Guard enforcement system in saddle/workflows/tdd-guard/. This should:

1. tdd_guard.py - Main enforcement script that:
   - Accepts a file path and intended action (write/edit) as arguments
   - For implementation files (*.py, *.js, *.ts excluding tests):
     - Checks if corresponding test file exists
     - If test file doesn't exist: BLOCK and output instructions to create test first
     - If test file exists but has no test for the function being modified: WARN
     - If tests exist: ALLOW
   - Returns exit code 0 (allow), 1 (block), or 2 (warn)
   - Outputs structured JSON with action, reason, and guidance

2. config.yaml - Configuration file specifying:
   - test_patterns: mapping of source patterns to test patterns
     - "src/**/*.py" -> "tests/**/test_*.py"
     - "src/**/*.js" -> "tests/**/*.test.js"
     - "lib/**/*.ts" -> "tests/**/*.spec.ts"
   - excluded_paths: files that don't require tests
     - "**/migrations/**"
     - "**/config/**"
     - "**/__init__.py"
   - strict_mode: boolean (block on warn if true)
   - custom_rules: list of additional patterns

3. README.md explaining:
   - How TDD Guard works
   - How to configure for different project structures
   - How to disable for specific files
   - Why mechanical enforcement matters (cite: 2x dev time but consistent quality)

Use pathlib for cross-platform paths. Use tree-sitter-languages for parsing if checking function-level test coverage.
```

### Prompt 4: Create Documentation Verification System

```
Create the documentation verification system in saddle/workflows/doc-verify/. This should:

1. doc_verify.py - Script that:
   - Runs as a pre-commit hook
   - Checks if modified files have corresponding documentation updates
   - Rules:
     - New Python module -> requires docstring
     - New public function -> requires docstring
     - Modified API endpoint -> requires API doc update or CHANGELOG entry
     - New feature (detected via commit message or file patterns) -> requires README mention
   - Outputs missing documentation as actionable checklist
   - Returns exit code 0 (pass) or 1 (fail with details)

2. templates/ folder with:
   - module_docstring.md - template for module-level documentation
   - function_docstring.md - template for function documentation
   - changelog_entry.md - template for CHANGELOG entries
   - api_doc.md - template for API documentation

3. Integration with git:
   - Detect changed files via git diff
   - Parse Python AST for new/modified functions
   - Check corresponding doc files for updates

The goal is to catch documentation gaps BEFORE commit, not enforce specific documentation style.
```

### Prompt 5: Create Auto-Indexing System

```
Create the codebase auto-indexing system in saddle/index/generator/. This should:

1. index_generator.py - Main orchestrator that:
   - Walks project/ directory
   - Dispatches to language-specific parsers
   - Generates four output files:
     a. codebase-index.json: {file: {functions: [], classes: [], imports: []}}
     b. dependency-graph.json: {module: [depends_on_modules]}
     c. stale-files.json: {file: {last_modified, last_referenced, staleness_score}}
     d. CODEBASE.md: Human-readable index with sections:
        - Directory structure (tree format)
        - Key entry points
        - Module dependency summary
        - Recently modified files
        - Potentially stale files

2. parsers/python_parser.py:
   - Uses ast module for Python files
   - Extracts: functions, classes, imports, decorators, docstrings
   - Builds import graph

3. parsers/js_parser.py:
   - Uses tree-sitter-languages for JS/TS
   - Extracts: functions, classes, imports/exports, React components
   - Handles ES6 modules and CommonJS

4. parsers/generic_parser.py:
   - Fallback for unsupported languages
   - Uses tree-sitter with language detection
   - Extracts basic structure (functions, classes)

5. embeddings/embed_code.py (optional, for semantic search):
   - Chunks code files by function/class
   - Generates embeddings using sentence-transformers
   - Stores in ChromaDB for semantic queries
   - Provides query interface: "Where is authentication handled?"

The index should regenerate:
- On git commit (via pre-commit hook)
- On manual trigger (/index command)
- Incrementally when possible (only changed files)

CRITICAL: The CODEBASE.md file should be concise. It's meant to be read by Claude at session start, not as comprehensive documentation. Target under 500 lines for projects up to 10k LOC.
```

### Prompt 6: Create Cleanup System

```
Create the cleanup and archival system in saddle/cleanup/. This should:

1. dead_code_detector.py:
   - Wrapper around vulture and deadcode
   - Runs both tools with project-appropriate settings
   - Deduplicates and ranks findings by:
     - Confidence score (vulture)
     - Code size (larger = higher priority)
     - File age (older unused code = higher priority)
   - Outputs actionable report with suggested removals
   - Supports --dry-run and --auto-fix modes

2. stale_file_tracker.py:
   - Uses gitpython to analyze commit history
   - Identifies files not modified in configurable period (default: 6 months)
   - Cross-references with import analysis (unused imports = stale indicator)
   - Checks for orphaned files (JSON, MD, config) not referenced anywhere
   - Generates stale-files.json consumed by index generator

3. archive_manager.py:
   - Workflow automation for archival decisions
   - Commands:
     - archive <path> - moves to .archive/ with metadata
     - list-archived - shows archived files with reasons
     - restore <path> - restores from archive
     - purge-archive --older-than 1y - permanent deletion
   - Creates .archive/manifest.json tracking:
     - Original path
     - Archive date
     - Reason (manual, stale, dead-code)
     - Restore instructions

The cleanup system should be non-destructive by default. All operations should be reversible until explicit purge.
```

### Prompt 7: Create Hook Configurations

```
Create the Claude Code hook system in .claude/. This should:

1. settings.json:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python saddle/workflows/tdd-guard/tdd_guard.py \"$FILE_PATH\" \"$ACTION\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python saddle/workflows/doc-verify/doc_verify.py --check-staged"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "cat saddle/rules/universal.md && cat saddle/index/CODEBASE.md | head -100"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow_shell": true,
    "allow_file_write": true,
    "require_approval_for": ["rm -rf", "git push", "terraform apply", "kubectl delete"]
  }
}
```

2. hooks/pre-tool-use.sh - Shell wrapper that:
   - Receives tool name, file path, and action
   - Dispatches to appropriate Python scripts
   - Handles exit codes (0=allow, 1=block, 2=warn)
   - Formats output for Claude Code consumption

3. hooks/post-tool-use.sh - Shell wrapper that:
   - Runs after successful tool use
   - Triggers documentation checks
   - Updates todo.md if configured
   - Logs action for audit trail

4. hooks/session-start.sh - Shell wrapper that:
   - Outputs key rules and context
   - Shows current todo.md state
   - Reports any blocking issues (failing tests, missing docs)
   - Runs quick index freshness check

Explain in comments why each hook exists and what failure modes it prevents.
```

### Prompt 8: Create Pre-commit Configuration

```
Create .pre-commit-config.yaml with these hooks:

repos:
  # Python linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Dead code detection
  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.11
    hooks:
      - id: vulture
        args: [project/, --min-confidence, "80"]

  # Security scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: [-r, project/, -ll]

  # Custom hooks
  - repo: local
    hooks:
      - id: tdd-guard
        name: TDD Guard
        entry: python saddle/workflows/tdd-guard/tdd_guard.py
        language: python
        types: [python]
        pass_filenames: true
        
      - id: doc-verify
        name: Documentation Verification
        entry: python saddle/workflows/doc-verify/doc_verify.py
        language: python
        pass_filenames: false
        stages: [commit]
        
      - id: update-index
        name: Update Codebase Index
        entry: python saddle/index/generator/index_generator.py --incremental
        language: python
        pass_filenames: false
        stages: [commit]
        always_run: true

Also create a brief explanation of each hook's purpose and how to skip specific hooks when necessary (SKIP=hook-id git commit).
```

### Prompt 9: Create Project Integration Scripts

```
Create the scripts/ directory with setup and integration scripts:

1. setup.sh:
   - Creates virtual environment
   - Installs Python dependencies from pyproject.toml
   - Installs pre-commit hooks
   - Initializes saddle directories
   - Creates initial index files
   - Outputs setup completion message with next steps

2. init-submodule.sh <repo-url> [branch]:
   - Adds client repository as git submodule in project/
   - Copies saddle/templates/project-claude.md to project/CLAUDE.md
   - Runs initial index generation
   - Outputs instructions for submodule workflow
   WHY: Submodules keep client code as separate git history, useful for:
   - Client repos you don't own
   - Tracking upstream changes
   - Clean separation of saddle and project commits

3. init-nested.sh [source-path]:
   - If source-path provided: copies code into project/
   - If no source-path: creates empty project structure
   - Initializes project/CLAUDE.md from template
   - Runs initial index generation
   WHY: Nested folders simplify workflow when:
   - Starting new projects
   - Working with code you'll modify heavily
   - Client prefers single-repo delivery

4. generate-index.sh [--full|--incremental]:
   - Triggers index regeneration
   - --full: Complete rebuild
   - --incremental: Only changed files (default)
   - Outputs index statistics and any warnings

5. run-cleanup.sh [--report|--fix]:
   - Runs dead code detection
   - Runs stale file tracking
   - --report: Output findings only (default)
   - --fix: Apply safe auto-fixes (with confirmation)
   - Outputs actionable cleanup plan

Each script should be executable, have a --help option, and include error handling with clear messages.
```

### Prompt 10: Create Template Files

```
Create the saddle/templates/ directory with starter templates:

1. project-claude.md - Template for project-specific CLAUDE.md:
```markdown
# Project: [PROJECT_NAME]

## Overview
[One paragraph describing what this project does]

## Key Paths
- Entry point: `src/main.py`
- API routes: `src/api/`
- Database models: `src/models/`
- Configuration: `config/`

## Critical Rules (Project-Specific)
- [Add rules that differ from or extend saddle defaults]

## Common Commands
```bash
# Run tests
pytest project/tests/

# Start development server
python project/src/main.py

# Run migrations
alembic upgrade head
```

## Architecture Notes
[Brief description of architecture patterns, key dependencies]

## Known Issues / Tech Debt
- [ ] [Track known issues here]
```

2. todo.md - External state file template:
```markdown
# Current Session: [DATE]

## Active Task
**Goal**: [What we're trying to accomplish]
**Status**: [Not Started | In Progress | Blocked | Complete]
**Blockers**: [Any blockers]

## Completed This Session
- [ ] [Track completed items]

## Next Steps
1. [Next action]
2. [Following action]

## Notes
[Session notes, decisions made, context to preserve]
```

3. assessment.md - Pre-coding assessment template:
```markdown
# Task Assessment: [TASK_NAME]

## Objective
[Clear statement of what needs to be accomplished]

## Scope
- Files to modify: [list]
- New files needed: [list]
- Tests required: [list]

## Approach
[Planned implementation approach]

## Risks & Considerations
- [Risk 1]
- [Risk 2]

## Dependencies
- [External dependencies]
- [Internal dependencies]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Estimated Complexity
[Low | Medium | High] - [Brief justification]

---
**Approval**: [ ] Proceed with implementation
```

Each template should be minimal but complete. The goal is reducing cognitive load, not creating bureaucracy.
```

---

## Tool Configurations

### Why These Tools?

| Tool | Purpose | Why This Choice |
|------|---------|-----------------|
| **tree-sitter-languages** | Multi-language parsing | Pre-compiled binaries for 100+ languages. No per-language setup. Works across any client stack. |
| **vulture** | Dead Python code detection | Most established tool, confidence scoring, whitelist support. |
| **deadcode** | Dead code with auto-fix | Newer tool with --fix capability. Complements vulture. |
| **gitpython** | Git history analysis | Pythonic interface for staleness detection, no subprocess calls. |
| **chromadb** | Vector storage | Embedded database, no server required. Portable across clients. |
| **sentence-transformers** | Code embeddings | Good balance of quality and speed for semantic code search. |
| **ruff** | Linting + formatting | Single tool replaces black, isort, flake8. Fast. |
| **bandit** | Security scanning | Catches common Python security issues pre-commit. |

### Optional Enhancements

**Neo4j** (for large codebases): When `dependency-graph.json` becomes unwieldy (>1000 modules), export to Neo4j for Cypher queries:
```cypher
-- Find all modules that depend on a deprecated module
MATCH (m:Module)-[:IMPORTS*]->(deprecated:Module {name: 'old_auth'})
RETURN m.name
```

**Qdrant** (for production semantic search): ChromaDB works for local development. Qdrant provides better performance for team-shared indexes.

---

## CLAUDE.md Architecture

### Hierarchy and Loading

Claude Code loads CLAUDE.md files hierarchically:

```
~/.claude/CLAUDE.md           # Global (user-level) - rarely needed
./CLAUDE.md                   # Repository root - saddle rules
./project/CLAUDE.md           # Project-specific - client context
./project/src/api/CLAUDE.md   # Subdirectory - API-specific patterns
```

Later files can override earlier ones. Use this strategically:

- **Saddle CLAUDE.md**: Universal rules, never overridden
- **Project CLAUDE.md**: Client-specific context, can adjust saddle defaults
- **Subdirectory CLAUDE.md**: Deep specialization (rare, use sparingly)

### Size Guidelines

| File | Target Size | Content |
|------|-------------|---------|
| Saddle CLAUDE.md | <150 lines | Rules hub, workflow triggers, command shortcuts |
| Project CLAUDE.md | <100 lines | Project-specific overrides, key paths, common commands |
| Rule files | <50 lines each | Single-topic detailed rules |
| CODEBASE.md | <500 lines | Auto-generated index, refreshed per-commit |

**Why size limits?** Claude's effective attention degrades with context length. A 500-line CLAUDE.md file means later rules receive less attention than earlier ones. Modular files loaded on-demand keep relevant rules in high-attention positions.

### Rule Phrasing That Works

Research shows specific patterns improve compliance:

**High compliance:**
```markdown
NEVER deploy directly. All infrastructure changes MUST go through Terraform.
```

**Low compliance:**
```markdown
Please avoid deploying directly when possible. It's better to use IaC.
```

**Pattern**: Use NEVER, ALWAYS, MUST. Be specific about the action and the alternative.

---

## Hook System

### How Hooks Prevent Drift

Hooks are mechanical enforcement. They don't rely on Claude remembering rules—they intercept actions and verify compliance.

```
User: "Write the authentication module"
Claude: [Attempts to write src/auth.py]
  ↓
PreToolUse Hook fires
  ↓
tdd_guard.py checks: Does tests/test_auth.py exist?
  ↓
NO → Hook returns exit code 1, blocks write
  ↓
Claude receives: "BLOCKED: Test file required. Create tests/test_auth.py first."
  ↓
Claude: "I need to write the tests first. Creating tests/test_auth.py..."
```

This works even when Claude has "forgotten" TDD requirements deep in a session.

### Hook Types

| Hook | Trigger | Use Case |
|------|---------|----------|
| **PreToolUse** | Before tool execution | Block non-compliant actions |
| **PostToolUse** | After tool execution | Verify postconditions, update state |
| **SessionStart** | On /clear or new session | Refresh context, show current state |

### Customizing Hooks

To disable TDD Guard for a specific project (client doesn't want it):

```yaml
# project/.claude/settings.local.json (gitignored)
{
  "hooks": {
    "PreToolUse": []  # Disables all PreToolUse hooks
  }
}
```

To add project-specific hooks:

```yaml
# project/.claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python project/scripts/custom_check.py \"$FILE_PATH\""
          }
        ]
      }
    ]
  }
}
```

---

## Auto-Indexing System

### What Gets Indexed

The index generator produces four artifacts:

**1. codebase-index.json** - Structural map
```json
{
  "project/src/auth.py": {
    "functions": ["login", "logout", "verify_token"],
    "classes": ["AuthManager", "TokenStore"],
    "imports": ["jwt", "bcrypt", "project.src.models.user"]
  }
}
```
**Use case**: "What functions are in auth.py?" → Read index, don't read file.

**2. dependency-graph.json** - Import relationships
```json
{
  "project.src.auth": ["jwt", "bcrypt", "project.src.models.user"],
  "project.src.api.routes": ["project.src.auth", "project.src.models"]
}
```
**Use case**: "What depends on the user model?" → Query graph, find all importers.

**3. stale-files.json** - Archival candidates
```json
{
  "project/scripts/old_migration.py": {
    "last_modified": "2024-01-15",
    "last_referenced": null,
    "staleness_score": 0.9
  }
}
```
**Use case**: Cleanup prompts prioritize high-staleness files.

**4. CODEBASE.md** - Human/AI readable summary
```markdown
# Codebase Index

## Structure
project/
├── src/
│   ├── api/          # REST API routes
│   ├── models/       # Database models
│   └── services/     # Business logic
├── tests/
└── config/

## Entry Points
- API: project/src/api/main.py
- CLI: project/src/cli.py

## Key Modules
- Authentication: project/src/auth.py (AuthManager, TokenStore)
- User management: project/src/models/user.py

## Recent Changes (last 7 days)
- project/src/api/routes.py (2 commits)
- project/tests/test_auth.py (1 commit)

## Potentially Stale
- project/scripts/old_migration.py (not modified in 6 months, no references)
```
**Use case**: Claude reads this at session start instead of exploring filesystem.

### Incremental Updates

Full index regeneration is expensive for large codebases. The generator supports incremental mode:

```bash
# Full rebuild
python saddle/index/generator/index_generator.py --full

# Only changed files (via git diff)
python saddle/index/generator/index_generator.py --incremental
```

Incremental mode:
1. Gets changed files from `git diff HEAD~1`
2. Re-parses only those files
3. Updates affected entries in index files
4. Regenerates CODEBASE.md summary

---

## Use Cases & Examples

### Use Case 1: New Client Project (Greenfield)

**Scenario**: Starting a new FastAPI project for a client.

```bash
# Initialize saddle
./scripts/setup.sh

# Create empty project structure
./scripts/init-nested.sh

# Edit project/CLAUDE.md with client specifics
claude "Update project/CLAUDE.md for a FastAPI project with PostgreSQL and Alembic migrations"
```

**Session workflow**:
```
You: Create the user authentication system

Claude: I'll start with the assessment phase since this is a substantial feature.
[Creates saddle/templates/assessment.md for auth system]
[Fills in scope, approach, risks]

Claude: Assessment complete. Key points:
- 3 files to create: auth.py, test_auth.py, routes/auth.py
- Using JWT with bcrypt
- Tests first per TDD Guard requirements

Shall I proceed?

You: Yes

Claude: Starting with tests...
[Creates tests/test_auth.py with test cases]
[TDD Guard allows because test file now exists]
[Creates src/auth.py implementation]
[Creates src/api/routes/auth.py]
[Updates CODEBASE.md index]
```

### Use Case 2: Existing Client Codebase (Brownfield)

**Scenario**: Taking over maintenance of a legacy Django project.

```bash
# Initialize saddle
./scripts/setup.sh

# Add existing repo as submodule
./scripts/init-submodule.sh git@github.com:client/legacy-app.git main

# Generate initial index (may take time for large codebase)
./scripts/generate-index.sh --full

# Review stale files
./scripts/run-cleanup.sh --report
```

**First session**:
```
You: What's the architecture of this project?

Claude: [Reads saddle/index/CODEBASE.md]
Based on the generated index:
- Django 3.2 project with 47 models
- Entry point: project/manage.py
- Key apps: users, billing, reporting
- 12 files flagged as potentially stale (no modifications in 6+ months)
- Dependency graph shows circular import between billing and reporting

Would you like me to detail any specific area?

You: Show me the circular import

Claude: [Reads dependency-graph.json]
The cycle is:
- billing.services imports reporting.generators
- reporting.generators imports billing.models
- billing.models imports billing.services (circular)

This is a common Django pattern issue. Options to resolve:
1. Move shared models to a core app
2. Use lazy imports
3. Restructure the dependency direction

Want me to create an assessment for fixing this?
```

### Use Case 3: Multi-Client Workflow

**Scenario**: Consultant managing multiple client projects.

```
~/work/
├── claude-code-saddle/          # Shared saddle (template)
├── client-a/
│   ├── CLAUDE.md                 # Symlink to saddle
│   ├── saddle/                  # Symlink to shared saddle
│   └── project/                  # Client A code (submodule)
├── client-b/
│   ├── CLAUDE.md
│   ├── saddle/
│   └── project/                  # Client B code (nested)
```

**Setup for new client**:
```bash
# Clone saddle template
cp -r claude-code-saddle client-c
cd client-c

# Add client code
./scripts/init-submodule.sh git@github.com:client-c/their-app.git

# Customize for their stack (Terraform + AWS)
echo "ALWAYS use Terraform for AWS resources. No direct AWS CLI." >> CLAUDE.md
```

Each client directory is self-contained with shared tooling.

### Use Case 4: Deep Session Recovery

**Scenario**: Claude has lost track of TDD after 50+ messages in a complex debugging session.

**Without hooks** (failure mode):
```
You: Now implement the fix we discussed

Claude: [Writes src/payment.py directly]
[No tests, forgot TDD requirement 40 messages ago]
```

**With hooks** (enforced):
```
You: Now implement the fix we discussed

Claude: [Attempts to write src/payment.py]
[TDD Guard blocks: "Test file tests/test_payment.py exists but has no test for process_refund()"]

Claude: Right, I need to add the test first.
[Writes test_process_refund() in tests/test_payment.py]
[Now writes src/payment.py implementation]
[Tests pass]
```

The hook doesn't care that Claude forgot—it mechanically enforces the workflow.

### Use Case 5: Codebase Query Without Reading Files

**Scenario**: Finding all usages of a deprecated function.

**Without index**:
```
You: Where is calculate_legacy_tax used?

Claude: Let me search through the codebase...
[Reads 15 files]
[Uses 10k tokens on file contents]
Found in: billing.py, reports.py, api/tax.py
```

**With index**:
```
You: Where is calculate_legacy_tax used?

Claude: [Reads dependency-graph.json and codebase-index.json]
Based on the index, calculate_legacy_tax is defined in project/src/tax.py and imported by:
- project/src/billing.py
- project/src/reports.py
- project/src/api/tax_routes.py

The stale-files.json shows this function hasn't been modified in 8 months.

Would you like me to create an assessment for deprecating and replacing it?
```

Same answer, fraction of the tokens, no file reads.

---

## Appendix: Quick Reference

### Commands

| Command | Description |
|---------|-------------|
| `/index` | Regenerate CODEBASE.md and indexes |
| `/cleanup` | Run dead code and staleness detection |
| `/assess <task>` | Create assessment document before coding |
| `/todo` | Show current session todo.md |
| `./scripts/setup.sh` | Initial saddle setup |
| `./scripts/generate-index.sh` | Manual index regeneration |
| `./scripts/run-cleanup.sh` | Manual cleanup analysis |

### File Locations

| Purpose | Location |
|---------|----------|
| Universal rules | `./CLAUDE.md` |
| Project rules | `./project/CLAUDE.md` |
| Modular rules | `./saddle/rules/*.md` |
| Generated index | `./saddle/index/CODEBASE.md` |
| Session state | `./saddle/templates/todo.md` |
| Hook configs | `./.claude/settings.json` |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `SADDLE_STRICT_MODE` | Set to `1` to block on warnings |
| `SADDLE_SKIP_HOOKS` | Set to `1` to bypass all hooks |
| `SADDLE_INDEX_FULL` | Set to `1` to force full index rebuild |

---

## Changelog

- **v1.0.0** - Initial release with TDD Guard, doc verification, auto-indexing, and cleanup systems