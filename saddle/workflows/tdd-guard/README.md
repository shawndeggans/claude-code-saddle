# TDD Guard

Mechanical enforcement of test-driven development (TDD) for Claude Code Saddle.

## How It Works

TDD Guard intercepts file write/edit operations and checks if corresponding test files exist before allowing implementation changes. This enforces the "test first" principle by blocking operations when tests are missing.

```
User: "Write the authentication module"
Claude: [Attempts to write src/auth.py]
  ↓
PreToolUse Hook fires (pre-tool-use.py)
  ↓
tdd_guard.py checks: Does tests/test_auth.py exist?
  ↓
NO → Hook returns exit code 2, blocks write, stderr goes to Claude
  ↓
Claude receives: "TDD VIOLATION: No test file found for auth.py"
  ↓
Claude: "I need to write the tests first. Creating tests/test_auth.py..."
```

**Key insight**: Exit code 2 is the only mechanism that both blocks the operation AND feeds stderr back to Claude for feedback.

## Exit Codes

| Code | Action | Meaning |
|------|--------|---------|
| 0 | Allow | Proceed with operation |
| 2 | Block | Operation prevented, stderr message fed to Claude |

**Note**: Exit code 2 is specifically used because it's the only code that both blocks AND communicates with Claude via stderr. Other non-zero codes show errors to the user but don't reach Claude.

## Configuration

Edit `config.yaml` to customize behavior:

### Test Patterns

Map source file patterns to test file patterns:

```yaml
test_patterns:
  "src/**/*.py": "tests/**/test_*.py"
  "src/**/*.js": "tests/**/*.test.js"
```

### Excluded Paths

Files matching these patterns skip TDD enforcement:

```yaml
excluded_paths:
  - "**/migrations/**"
  - "**/__init__.py"
  - "**/conftest.py"
```

### Strict Mode

Enable strict mode to block on any missing coverage:

```yaml
strict_mode: true
```

## Per-File Overrides

To skip TDD enforcement for a specific file:

1. Create a `.tdd-skip` marker file in the same directory, or
2. Add the file pattern to `excluded_paths` in config.yaml

## Usage

### CLI

```bash
# Check a file
python tdd_guard.py src/auth.py write

# Check with strict mode
python tdd_guard.py src/auth.py edit --strict

# JSON output for programmatic use
python tdd_guard.py src/auth.py write --json
```

### As Hook

TDD Guard is invoked by the pre-tool-use.py hook, which reads JSON from stdin and calls tdd_guard.py:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/pre-tool-use.py"
          }
        ]
      }
    ]
  }
}
```

The pre-tool-use.py hook:
1. Reads JSON payload from stdin
2. Checks if TDD is enabled in `project/CLAUDE.md`
3. Calls tdd_guard.py for implementation files
4. Exits with code 2 (blocking) if no test file exists

## Why Mechanical Enforcement?

### The Problem

In long coding sessions, AI agents tend to "forget" rules from CLAUDE.md. This is especially common with TDD:

- Session starts with TDD commitment
- After 50+ messages of debugging, the agent writes code without tests
- Quality degrades gradually

### The Solution

Hooks don't rely on memory - they mechanically intercept operations:

- Every file write triggers TDD Guard (via pre-tool-use.py)
- No test file? Operation blocked with exit code 2
- Claude receives stderr message explaining what to do
- TDD enforced regardless of session length

Exit code 2 is the key: it's the only code that blocks AND feeds stderr to Claude.

### The Trade-off

TDD takes roughly 2x development time but provides:

- Fewer bugs in production
- Faster debugging (tests isolate issues)
- Safe refactoring (tests catch regressions)
- Living documentation (tests show usage)

For any code that will be maintained, this is a net positive.

## Troubleshooting

### "BLOCKED: No test file found"

Create the test file first:

```bash
# For src/module.py, create:
touch tests/test_module.py
```

Then add at least one test:

```python
def test_placeholder():
    """Placeholder test - implement real tests."""
    pass
```

### Test file exists but still blocked

In strict mode (`--strict` or `strict_mode: true` in config), incomplete coverage will also block. Add tests for all public functions.

### Skip TDD for specific files

Add to `excluded_paths` in config.yaml:

```yaml
excluded_paths:
  - "**/scripts/one_off_migration.py"
```

### Disable TDD Guard entirely

Set in your local settings:

```json
{
  "hooks": {
    "PreToolUse": []
  }
}
```
