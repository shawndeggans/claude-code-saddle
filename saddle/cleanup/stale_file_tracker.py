#!/usr/bin/env python3
"""Track stale files using git history and reference analysis.

This module identifies potentially stale files based on:
- Last modification date from git history
- Reference count (how many other files import/reference it)
- Orphaned status (files not referenced anywhere)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class StaleFile:
    """Information about a potentially stale file."""

    path: str
    last_modified: str
    days_since_modified: int
    reference_count: int
    staleness_score: float  # 0.0 to 1.0
    reasons: list[str]


def get_file_last_modified(file_path: Path, repo_path: Path | None = None) -> datetime | None:
    """Get last modification date from git history.

    Args:
        file_path: Path to the file.
        repo_path: Root of the git repository.

    Returns:
        Last modification datetime, or None if not found.
    """
    cwd = repo_path or Path.cwd()

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(file_path)],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None

        timestamp = int(result.stdout.strip())
        return datetime.fromtimestamp(timestamp)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return None


def find_references(file_path: Path, project_path: Path) -> list[str]:
    """Find files that reference the given file (imports, includes).

    Uses grep to find references to the module/file name.

    Args:
        file_path: Path to check references for.
        project_path: Root of the project.

    Returns:
        List of file paths that reference this file.
    """
    # Get the module name (without extension)
    stem = file_path.stem
    if stem == "__init__":
        # For __init__.py, use the parent directory name
        stem = file_path.parent.name

    references = []

    try:
        # Search for import statements or references
        patterns = [
            f"import {stem}",
            f"from {stem}",
            f"from .{stem}",
            f"require.*{stem}",
            f'"{stem}"',
            f"'{stem}'",
        ]

        for pattern in patterns:
            result = subprocess.run(
                ["grep", "-rl", pattern, str(project_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                for ref in result.stdout.strip().split("\n"):
                    if ref and ref != str(file_path):
                        references.append(ref)

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return list(set(references))


def calculate_staleness_score(
    days_since_modified: int,
    reference_count: int,
    threshold_days: int = 180,
) -> float:
    """Calculate staleness score (0.0 = fresh, 1.0 = very stale).

    Args:
        days_since_modified: Days since last modification.
        reference_count: Number of files referencing this one.
        threshold_days: Days threshold for staleness.

    Returns:
        Staleness score between 0.0 and 1.0.
    """
    # Age component: 0 at 0 days, 1 at threshold
    age_score = min(days_since_modified / threshold_days, 1.0)

    # Reference component: 0 if many references, 1 if none
    if reference_count == 0:
        ref_score = 1.0
    else:
        ref_score = max(0, 1 - reference_count / 10)

    # Weight: age is more important than references
    return age_score * 0.6 + ref_score * 0.4


def find_orphaned_files(project_path: Path) -> list[Path]:
    """Find files not referenced anywhere (JSON, MD, config files).

    Args:
        project_path: Root of the project.

    Returns:
        List of potentially orphaned file paths.
    """
    orphan_extensions = {".json", ".md", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
    orphans = []

    for path in project_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in orphan_extensions:
            continue

        # Skip common files that shouldn't be checked
        if path.name.lower() in {
            "readme.md",
            "changelog.md",
            "license.md",
            "contributing.md",
            "package.json",
            "pyproject.toml",
            "setup.py",
            ".gitignore",
        }:
            continue

        references = find_references(path, project_path)
        if not references:
            orphans.append(path)

    return orphans


def track_stale_files(
    project_path: Path,
    threshold_days: int = 180,
    include_orphans: bool = True,
) -> list[StaleFile]:
    """Identify stale files in project.

    Args:
        project_path: Root of project to analyze.
        threshold_days: Days without modification to consider stale.
        include_orphans: Include unreferenced config/data files.

    Returns:
        List of StaleFile entries sorted by staleness_score.
    """
    stale_files = []
    now = datetime.now()

    # Find Python files
    for path in project_path.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        if ".venv" in str(path) or "venv" in str(path):
            continue

        last_modified = get_file_last_modified(path, project_path)
        if last_modified is None:
            continue

        days_since = (now - last_modified).days
        if days_since < threshold_days:
            continue

        references = find_references(path, project_path)
        staleness_score = calculate_staleness_score(
            days_since, len(references), threshold_days
        )

        reasons = []
        if days_since >= threshold_days:
            reasons.append(f"not_modified_in_{days_since}_days")
        if len(references) == 0:
            reasons.append("not_referenced")

        stale_files.append(
            StaleFile(
                path=str(path.relative_to(project_path)),
                last_modified=last_modified.isoformat(),
                days_since_modified=days_since,
                reference_count=len(references),
                staleness_score=round(staleness_score, 2),
                reasons=reasons,
            )
        )

    # Add orphaned config/data files
    if include_orphans:
        for path in find_orphaned_files(project_path):
            last_modified = get_file_last_modified(path, project_path)
            days_since = (now - last_modified).days if last_modified else 365

            stale_files.append(
                StaleFile(
                    path=str(path.relative_to(project_path)),
                    last_modified=last_modified.isoformat() if last_modified else "",
                    days_since_modified=days_since,
                    reference_count=0,
                    staleness_score=0.9,  # High score for orphans
                    reasons=["orphaned", "not_referenced"],
                )
            )

    # Sort by staleness score
    return sorted(stale_files, key=lambda x: x.staleness_score, reverse=True)


def generate_stale_files_json(stale_files: list[StaleFile]) -> dict:
    """Generate stale-files.json content.

    Args:
        stale_files: List of stale file information.

    Returns:
        Dictionary suitable for JSON serialization.
    """
    return {
        sf.path: {
            "last_modified": sf.last_modified,
            "days_since_modified": sf.days_since_modified,
            "reference_count": sf.reference_count,
            "staleness_score": sf.staleness_score,
            "reasons": sf.reasons,
        }
        for sf in stale_files
    }


def format_text(stale_files: list[StaleFile]) -> str:
    """Format results as plain text.

    Args:
        stale_files: List of stale files.

    Returns:
        Text-formatted report.
    """
    if not stale_files:
        return "No stale files found."

    lines = [
        "Stale Files Report",
        "=" * 50,
        f"Found {len(stale_files)} potentially stale files",
        "",
    ]

    for sf in stale_files:
        score_pct = int(sf.staleness_score * 100)
        lines.append(
            f"[{score_pct:3d}%] {sf.path} "
            f"({sf.days_since_modified} days, {sf.reference_count} refs)"
        )
        for reason in sf.reasons:
            lines.append(f"       - {reason}")

    return "\n".join(lines)


def format_json(stale_files: list[StaleFile]) -> str:
    """Format results as JSON.

    Args:
        stale_files: List of stale files.

    Returns:
        JSON-formatted report.
    """
    return json.dumps(generate_stale_files_json(stale_files), indent=2)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Track stale files using git history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default="project/",
        help="Path to project directory (default: project/)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=180,
        help="Days without modification to consider stale (default: 180)",
    )
    parser.add_argument(
        "--no-orphans",
        action="store_true",
        help="Exclude orphaned config/data files",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write output to file",
    )

    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}")
        return 1

    stale_files = track_stale_files(
        project_path=project_path,
        threshold_days=args.threshold,
        include_orphans=not args.no_orphans,
    )

    if args.format == "json":
        output = format_json(stale_files)
    else:
        output = format_text(stale_files)

    if args.output:
        args.output.write_text(output)
        print(f"Output written to: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
