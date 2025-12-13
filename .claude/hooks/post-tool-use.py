#!/usr/bin/env python3
"""Post-tool-use hook for Claude Code Saddle.

This hook runs after Write/Edit operations and:
- Logs modifications to the session audit trail
- Optionally runs documentation verification (advisory)

This hook is INFORMATIONAL ONLY - it never blocks operations.

Exit Codes:
    0: Always (informational hook)
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
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


def is_test_file(file_path: str) -> bool:
    """Check if a file is a test file."""
    name = Path(file_path).name
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or "/tests/" in file_path
    )


def log_modification(repo_root: Path, file_path: str) -> None:
    """Log modification to session audit trail."""
    session_log = repo_root / ".session-log.txt"
    try:
        timestamp = datetime.now().isoformat(timespec="seconds")
        with open(session_log, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - Modified: {file_path}\n")
    except OSError:
        pass  # Silently ignore logging failures


def run_doc_verify(repo_root: Path, file_path: str) -> str | None:
    """Run documentation verification and return result if issues found."""
    doc_verify = repo_root / "saddle" / "workflows" / "doc-verify" / "doc_verify.py"

    if not doc_verify.exists():
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(doc_verify), "--files", file_path, "--format", "text"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        output = result.stdout.strip()
        if output and "All checks passed" not in output:
            return output
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return None


def main() -> int:
    """Main entry point."""
    # Read JSON payload from stdin
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    # Extract file path from tool input
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""

    if not file_path:
        return 0

    repo_root = get_repo_root()

    # Log the modification
    log_modification(repo_root, file_path)

    # Skip non-Python files for doc verification
    if not file_path.endswith(".py"):
        return 0

    # Skip test files
    if is_test_file(file_path):
        return 0

    # Run documentation verification (advisory)
    doc_result = run_doc_verify(repo_root, file_path)
    if doc_result:
        # Output to stdout as advisory message
        print(f"[DOC ADVISORY] {doc_result}")

    # Always exit 0 - this is an informational hook
    return 0


if __name__ == "__main__":
    sys.exit(main())
