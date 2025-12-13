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
import re
import subprocess
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Get the repository root directory."""
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


def is_tdd_enabled(repo_root: Path) -> bool:
    """Check if TDD enforcement is enabled."""
    project_claude = repo_root / "project" / "CLAUDE.md"
    if not project_claude.exists():
        return False

    try:
        content = project_claude.read_text(encoding="utf-8")
        pattern = r"^TDD:\s*enabled"
        return bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
    except OSError:
        return False


def has_test_files(repo_root: Path) -> bool:
    """Check if there are any test files to run."""
    test_dir = repo_root / "project" / "tests"
    if not test_dir.exists():
        return False

    # Check for any Python test files
    test_files = list(test_dir.glob("test_*.py"))
    return len(test_files) > 0


def run_tests(repo_root: Path) -> tuple[bool, str]:
    """Run pytest and return (passed, output)."""
    test_dir = repo_root / "project" / "tests"

    try:
        result = subprocess.run(
            ["pytest", str(test_dir), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
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

    repo_root = get_repo_root()

    # Only run test verification when TDD is enabled
    if not is_tdd_enabled(repo_root):
        return 0

    # Skip if no test files exist
    if not has_test_files(repo_root):
        return 0

    # Run tests
    passed, output = run_tests(repo_root)

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
