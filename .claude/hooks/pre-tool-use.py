#!/usr/bin/env python3
"""Pre-tool-use hook for Claude Code Saddle.

This hook enforces TDD requirements before Write/Edit operations.
When TDD is enabled and no test file exists, it BLOCKS the operation.

Exit Codes:
    0: Allow - proceed with operation
    2: Block - operation prevented, stderr message fed to Claude
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
    """Check if TDD enforcement is enabled in project/CLAUDE.md."""
    project_claude = repo_root / "project" / "CLAUDE.md"
    if not project_claude.exists():
        return False

    try:
        content = project_claude.read_text(encoding="utf-8")
        pattern = r"^TDD:\s*enabled"
        return bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
    except OSError:
        return False


def is_test_file(file_path: str) -> bool:
    """Check if a file is a test file."""
    name = Path(file_path).name
    stem = Path(file_path).stem

    # Python test patterns
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    if stem == "conftest":
        return True

    # JavaScript/TypeScript test patterns
    if name.endswith((".test.js", ".test.ts", ".spec.js", ".spec.ts")):
        return True

    # In a tests directory
    return "/tests/" in file_path or "/__tests__/" in file_path


def is_in_project_dir(file_path: str) -> bool:
    """Check if file is in the project/ directory."""
    return file_path.startswith("project/") or "/project/" in file_path


def run_tdd_guard(repo_root: Path, file_path: str) -> dict:
    """Run TDD Guard and return the result."""
    tdd_guard = repo_root / "saddle" / "workflows" / "tdd-guard" / "tdd_guard.py"

    if not tdd_guard.exists():
        return {"action": "allow", "reason": "TDD Guard not found"}

    try:
        result = subprocess.run(
            [sys.executable, str(tdd_guard), file_path, "write", "--json"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return {"action": "allow", "reason": "TDD Guard execution failed"}
    except subprocess.SubprocessError:
        return {"action": "allow", "reason": "TDD Guard execution failed"}


def main() -> int:
    """Main entry point."""
    # Read JSON payload from stdin
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Can't parse input, allow operation
        return 0

    # Extract file path from tool input
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""

    if not file_path:
        return 0

    repo_root = get_repo_root()

    # Check if TDD is enabled
    if not is_tdd_enabled(repo_root):
        return 0

    # Skip files outside project/ directory
    if not is_in_project_dir(file_path):
        return 0

    # Skip test files
    if is_test_file(file_path):
        return 0

    # Run TDD Guard
    result = run_tdd_guard(repo_root, file_path)
    action = result.get("action", "allow")

    if action == "block":
        # Output to stderr - this goes to Claude when we exit 2
        reason = result.get("reason", "No test file found")
        guidance = result.get("guidance", "")

        print(f"TDD VIOLATION: {reason}", file=sys.stderr)
        if guidance:
            print(f"Action required: {guidance}", file=sys.stderr)
        print("", file=sys.stderr)
        msg = "Create the test file first, then retry writing the implementation."
        print(msg, file=sys.stderr)

        # Exit 2 blocks the operation AND feeds stderr to Claude
        return 2

    # Allow operation
    return 0


if __name__ == "__main__":
    sys.exit(main())
