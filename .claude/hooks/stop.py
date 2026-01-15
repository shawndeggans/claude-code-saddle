#!/usr/bin/env python3
"""Stop hook for Claude Code Saddle.

This hook fires when Claude is about to finish responding.
It can block completion by outputting a JSON decision to stdout.

When TDD is enabled, this hook verifies that tests pass before
allowing task completion.

Exit Codes:
    0: Always (decision communicated via stdout JSON)

Output:
    JSON with {"decision": "block", "reason": "..."} to prevent completion
    Nothing or empty for normal completion
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_project_dir() -> Path:
    """Get the project directory from environment or git."""
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        return Path(env_dir)

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def is_tdd_enabled(project_dir: Path) -> bool:
    """Check if TDD enforcement is enabled."""
    project_claude = project_dir / "project" / "CLAUDE.md"
    if not project_claude.exists():
        return False

    try:
        content = project_claude.read_text(encoding="utf-8")
        pattern = r"^TDD:\s*enabled"
        return bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
    except OSError:
        return False


def has_test_files(project_dir: Path) -> bool:
    """Check if there are any test files to run."""
    test_dir = project_dir / "project" / "tests"
    if not test_dir.exists():
        return False

    # Check for any Python test files
    test_files = list(test_dir.glob("test_*.py"))
    return len(test_files) > 0


def update_context_snapshot(project_dir: Path) -> None:
    """Update context snapshot with current session state."""
    snapshot_path = project_dir / "saddle" / "sessions" / "context-snapshot.md"

    try:
        # Get recent git activity
        git_log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
        ).stdout.strip()

        git_diff = subprocess.run(
            ["git", "diff", "--stat", "HEAD~3..HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
        ).stdout.strip()

        git_status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
        ).stdout.strip()

        # Build snapshot
        snapshot = f"""# Context Snapshot
Auto-generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Recent Commits
```
{git_log}
```

## Recent Changes
```
{git_diff if git_diff else "(no recent changes)"}
```

## Uncommitted Work
```
{git_status if git_status else "(clean)"}
```

## Session Notes
(Add manual notes here if needed)

"""

        # Write snapshot
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(snapshot, encoding="utf-8")

    except (subprocess.SubprocessError, OSError):
        pass  # Silently ignore snapshot failures


def run_tests(project_dir: Path) -> tuple[bool, str]:
    """Run pytest and return (passed, output)."""
    test_dir = project_dir / "project" / "tests"

    try:
        result = subprocess.run(
            ["pytest", str(test_dir), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=60,
        )
        output = result.stdout + result.stderr

        # pytest returns 0 on success, non-zero on failure
        passed = result.returncode == 0
        return passed, output

    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 60 seconds"
    except FileNotFoundError:
        # pytest not installed
        return True, "pytest not installed, skipping test verification"
    except subprocess.SubprocessError as e:
        return False, f"Failed to run tests: {e}"


def main() -> int:
    """Main entry point."""
    # Read JSON payload from stdin
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    # CRITICAL: Check stop_hook_active to prevent infinite loops
    # If this is true, we're being called again after blocking
    if payload.get("stop_hook_active"):
        return 0

    project_dir = get_project_dir()

    # Update context snapshot on clean exit
    update_context_snapshot(project_dir)

    # Only run test verification when TDD is enabled
    if not is_tdd_enabled(project_dir):
        return 0

    # Skip if no test files exist
    if not has_test_files(project_dir):
        return 0

    # Run tests
    passed, output = run_tests(project_dir)

    if not passed:
        # Block completion - tests are failing
        truncated_output = output[:500]
        reason = f"Tests are failing. Fix them before completing.\n\n{truncated_output}"
        decision = {"decision": "block", "reason": reason}
        print(json.dumps(decision))

    # Exit 0 - decision communicated via stdout
    return 0


if __name__ == "__main__":
    sys.exit(main())
