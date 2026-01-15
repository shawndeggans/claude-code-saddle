#!/usr/bin/env python3
"""PreCompact hook for Claude Code Saddle.

This hook fires before /clear or auto-compaction.
It saves a context snapshot so the next session can recover state.

Exit Codes:
    0: Always (snapshot saved, stdout injected into context)
"""

from __future__ import annotations

import json
import os
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


def main() -> int:
    """Main entry point."""
    project_dir = get_project_dir()
    snapshot_path = project_dir / "saddle" / "sessions" / "context-snapshot.md"

    try:
        # Read recent git activity
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

        # Output for Claude
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreCompact",
                "additionalContext": f"Context snapshot saved to {snapshot_path}",
            }
        }
        print(json.dumps(output))

    except (subprocess.SubprocessError, OSError) as e:
        # Output error but don't block
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreCompact",
                "additionalContext": f"Failed to save context snapshot: {e}",
            }
        }
        print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
