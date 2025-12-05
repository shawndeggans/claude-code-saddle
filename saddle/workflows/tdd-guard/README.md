# TDD Guard

Mechanical enforcement of test-driven development (TDD) for Claude Code Saddle.

## How It Works

TDD Guard intercepts file write/edit operations and checks if corresponding test files exist before allowing implementation changes. This enforces the "test first" principle by blocking operations when tests are missing.

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

## Exit Codes

| Code | Action | Meaning |
|------|--------|---------|
| 0 | Allow | Proceed with operation |
| 1 | Block | Operation prevented, create tests first |
| 2 | Warn | Operation allowed but tests are incomplete |

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

TDD Guard is typically invoked by the Claude Code PreToolUse hook:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python saddle/workflows/tdd-guard/tdd_guard.py \"$FILE_PATH\" write"
          }
        ]
      }
    ]
  }
}
```

## Why Mechanical Enforcement?

### The Problem

In long coding sessions, AI agents tend to "forget" rules from CLAUDE.md. This is especially common with TDD:

- Session starts with TDD commitment
- After 50+ messages of debugging, the agent writes code without tests
- Quality degrades gradually

### The Solution

Hooks don't rely on memory - they mechanically intercept operations:

- Every file write triggers TDD Guard
- No test file? Operation blocked
- Agent receives clear instructions
- TDD enforced regardless of session length

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

### "WARN: Missing test coverage"

The test file exists but doesn't cover all functions. Add tests for the listed functions.

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
