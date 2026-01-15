#!/usr/bin/env python3
"""User prompt submit hook for Claude Code Saddle.

This hook fires before Claude processes a user prompt.
Its stdout is injected into Claude's context, allowing us to
inject engineering requirements and reminders.

Exit Codes:
    0: Always (stdout injected into context)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
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


def get_index_status(project_dir: Path) -> str:
    """Check if codebase index exists and is recent."""
    index_path = project_dir / "saddle" / "index" / "CODEBASE.md"
    if index_path.exists():
        return "available"
    return "not found"


def main() -> int:
    """Main entry point."""
    # Read JSON payload from stdin (we don't use it, but validate it)
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    project_dir = get_project_dir()
    tdd_enabled = is_tdd_enabled(project_dir)
    index_status = get_index_status(project_dir)

    # Build requirements message to inject into context
    requirements = []

    requirements.append("SADDLE ENGINEERING REQUIREMENTS:")
    requirements.append("")

    # Index reminder
    if index_status == "available":
        requirements.append(
            "- Check saddle/index/CODEBASE.md before exploring the filesystem"
        )

    # TDD enforcement
    if tdd_enabled:
        requirements.append(
            "- TDD ENFORCEMENT ACTIVE: Create test files BEFORE implementation"
        )
        requirements.append(
            "- Test files must exist before you can write implementation files"
        )
    else:
        requirements.append("- Run tests after writing implementation code")

    # Standard requirements
    requirements.append(
        "- For changes touching 3+ files, state your approach before starting"
    )
    requirements.append("- Run 'pytest project/tests/' before committing")

    # Output structured JSON
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n".join(requirements),
        }
    }
    print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
