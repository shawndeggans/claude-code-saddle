#!/usr/bin/env python3
"""Session start hook for Claude Code Saddle.

This hook fires when a new Claude Code session begins.
It injects context including:
- Saddle status
- Context snapshot (if exists from previous session)
- Current git status

Exit Codes:
    0: Always (stdout injected into context)
"""

from __future__ import annotations

import json
import os
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


def get_git_status(project_dir: Path) -> str:
    """Get current git status."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def load_context_snapshot(project_dir: Path) -> str | None:
    """Load context snapshot if it exists."""
    snapshot_path = project_dir / "saddle" / "sessions" / "context-snapshot.md"
    if snapshot_path.exists():
        try:
            return snapshot_path.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


def main() -> int:
    """Main entry point."""
    project_dir = get_project_dir()
    context_parts = ["Saddle active."]

    # Check for codebase index
    index_path = project_dir / "saddle" / "index" / "CODEBASE.md"
    if index_path.exists():
        context_parts.append("Index: saddle/index/CODEBASE.md")

    # Load context snapshot if exists
    snapshot = load_context_snapshot(project_dir)
    if snapshot:
        context_parts.append("\n## Previous Context")
        context_parts.append(snapshot)

    # Current git status
    git_status = get_git_status(project_dir)
    if git_status:
        context_parts.append("\n## Current Uncommitted Changes")
        context_parts.append(f"```\n{git_status}\n```")
    else:
        context_parts.append("\nWorking tree clean.")

    # Output structured JSON
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(context_parts),
        }
    }
    print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
