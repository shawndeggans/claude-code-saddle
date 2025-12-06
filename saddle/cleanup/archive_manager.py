#!/usr/bin/env python3
"""Archive workflow automation for code cleanup.

This module provides a non-destructive archival system for managing
dead or stale code. Files are moved to an .archive directory with
metadata, allowing easy restoration if needed.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

ARCHIVE_DIR = ".archive"
MANIFEST_FILE = "manifest.json"


@dataclass
class ArchiveEntry:
    """Metadata for an archived file."""

    original_path: str
    archive_path: str
    archived_at: str
    reason: str  # "manual", "stale", "dead-code"
    size_bytes: int
    metadata: dict


def load_manifest(repo_path: Path) -> dict[str, ArchiveEntry]:
    """Load archive manifest.

    Args:
        repo_path: Root of the repository.

    Returns:
        Dictionary mapping original paths to ArchiveEntry.
    """
    manifest_path = repo_path / ARCHIVE_DIR / MANIFEST_FILE
    if not manifest_path.exists():
        return {}

    try:
        data = json.loads(manifest_path.read_text())
        return {k: ArchiveEntry(**v) for k, v in data.items()}
    except (json.JSONDecodeError, TypeError):
        return {}


def save_manifest(repo_path: Path, manifest: dict[str, ArchiveEntry]) -> None:
    """Save archive manifest.

    Args:
        repo_path: Root of the repository.
        manifest: Manifest dictionary to save.
    """
    manifest_path = repo_path / ARCHIVE_DIR / MANIFEST_FILE
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    data = {k: asdict(v) for k, v in manifest.items()}
    manifest_path.write_text(json.dumps(data, indent=2))


def archive_file(
    file_path: Path,
    repo_path: Path,
    reason: str = "manual",
    metadata: dict | None = None,
) -> ArchiveEntry:
    """Archive a file by moving it to .archive/ with metadata.

    Args:
        file_path: Path to file to archive.
        repo_path: Repository root.
        reason: Why file is being archived.
        metadata: Additional metadata to store.

    Returns:
        ArchiveEntry for the archived file.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file is already archived.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get relative path
    try:
        relative_path = file_path.relative_to(repo_path)
    except ValueError:
        relative_path = file_path

    # Check if already archived
    manifest = load_manifest(repo_path)
    if str(relative_path) in manifest:
        raise ValueError(f"File already archived: {relative_path}")

    # Create archive path (preserve directory structure)
    archive_dir = repo_path / ARCHIVE_DIR
    archive_path = archive_dir / relative_path
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    # Get file size before moving
    size_bytes = file_path.stat().st_size

    # Move file to archive
    shutil.move(str(file_path), str(archive_path))

    # Create entry
    entry = ArchiveEntry(
        original_path=str(relative_path),
        archive_path=str(archive_path.relative_to(repo_path)),
        archived_at=datetime.now().isoformat(),
        reason=reason,
        size_bytes=size_bytes,
        metadata=metadata or {},
    )

    # Update manifest
    manifest[str(relative_path)] = entry
    save_manifest(repo_path, manifest)

    return entry


def restore_file(original_path: str, repo_path: Path) -> bool:
    """Restore a file from archive to its original location.

    Args:
        original_path: Original path of the file.
        repo_path: Repository root.

    Returns:
        True if restored successfully, False otherwise.
    """
    manifest = load_manifest(repo_path)
    if original_path not in manifest:
        print(f"File not in archive: {original_path}")
        return False

    entry = manifest[original_path]
    archive_path = repo_path / entry.archive_path
    restore_path = repo_path / entry.original_path

    if not archive_path.exists():
        print(f"Archived file missing: {archive_path}")
        return False

    # Ensure parent directory exists
    restore_path.parent.mkdir(parents=True, exist_ok=True)

    # Move back
    shutil.move(str(archive_path), str(restore_path))

    # Update manifest
    del manifest[original_path]
    save_manifest(repo_path, manifest)

    # Clean up empty directories in archive
    try:
        archive_path.parent.rmdir()
    except OSError:
        pass  # Directory not empty

    return True


def list_archived(repo_path: Path) -> list[ArchiveEntry]:
    """List all archived files with their metadata.

    Args:
        repo_path: Repository root.

    Returns:
        List of ArchiveEntry objects.
    """
    manifest = load_manifest(repo_path)
    return list(manifest.values())


def purge_archive(
    repo_path: Path,
    older_than_days: int | None = None,
    dry_run: bool = True,
) -> list[str]:
    """Permanently delete archived files.

    Args:
        repo_path: Repository root.
        older_than_days: Only purge files archived more than N days ago.
        dry_run: If True, only report what would be purged.

    Returns:
        List of purged file paths.
    """
    manifest = load_manifest(repo_path)
    purged = []
    now = datetime.now()

    for original_path, entry in list(manifest.items()):
        # Check age filter
        if older_than_days is not None:
            archived_at = datetime.fromisoformat(entry.archived_at)
            days_archived = (now - archived_at).days
            if days_archived < older_than_days:
                continue

        archive_path = repo_path / entry.archive_path

        if dry_run:
            print(f"Would purge: {original_path}")
        else:
            if archive_path.exists():
                archive_path.unlink()
            del manifest[original_path]
            print(f"Purged: {original_path}")

        purged.append(original_path)

    if not dry_run:
        save_manifest(repo_path, manifest)

    return purged


def parse_duration(duration_str: str) -> int:
    """Parse duration string like '1y', '6m', '30d' to days.

    Args:
        duration_str: Duration string.

    Returns:
        Number of days.
    """
    if not duration_str:
        return 0

    unit = duration_str[-1].lower()
    try:
        value = int(duration_str[:-1])
    except ValueError:
        return 0

    if unit == "d":
        return value
    elif unit == "w":
        return value * 7
    elif unit == "m":
        return value * 30
    elif unit == "y":
        return value * 365
    else:
        return int(duration_str)


def format_list(entries: list[ArchiveEntry]) -> str:
    """Format archive list for display.

    Args:
        entries: List of archive entries.

    Returns:
        Formatted string.
    """
    if not entries:
        return "Archive is empty."

    lines = [
        "Archived Files",
        "=" * 50,
        f"Total: {len(entries)} files",
        "",
    ]

    for entry in entries:
        date = entry.archived_at[:10]
        size_kb = entry.size_bytes / 1024
        lines.append(
            f"[{date}] {entry.original_path} ({size_kb:.1f} KB) - {entry.reason}"
        )

    return "\n".join(lines)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage archived code files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  archive <path>           Archive a file
  restore <path>           Restore from archive
  list                     List archived files
  purge                    Permanently delete archived files

Examples:
  archive_manager.py archive src/old_module.py
  archive_manager.py restore src/old_module.py
  archive_manager.py list
  archive_manager.py purge --older-than 1y
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # archive command
    archive_parser = subparsers.add_parser("archive", help="Archive a file")
    archive_parser.add_argument("path", help="File to archive")
    archive_parser.add_argument(
        "--reason",
        default="manual",
        help="Reason for archiving (default: manual)",
    )

    # restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from archive")
    restore_parser.add_argument("path", help="Original path to restore")

    # list command
    subparsers.add_parser("list", help="List archived files")

    # purge command
    purge_parser = subparsers.add_parser("purge", help="Permanently delete")
    purge_parser.add_argument(
        "--older-than",
        help="Only purge files older than (e.g., '1y', '6m', '30d')",
    )
    purge_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be purged without deleting",
    )
    purge_parser.add_argument(
        "--force",
        action="store_true",
        help="Actually delete (required without --dry-run)",
    )

    args = parser.parse_args()
    repo_path = Path.cwd()

    if args.command == "archive":
        file_path = Path(args.path)
        if not file_path.is_absolute():
            file_path = repo_path / file_path

        try:
            entry = archive_file(file_path, repo_path, reason=args.reason)
            print(f"Archived: {entry.original_path}")
            print(f"Location: {entry.archive_path}")
            return 0
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return 1

    elif args.command == "restore":
        if restore_file(args.path, repo_path):
            print(f"Restored: {args.path}")
            return 0
        else:
            return 1

    elif args.command == "list":
        entries = list_archived(repo_path)
        print(format_list(entries))
        return 0

    elif args.command == "purge":
        if not args.dry_run and not args.force:
            print("Error: Use --dry-run to preview or --force to actually delete")
            return 1

        older_than = parse_duration(args.older_than) if args.older_than else None
        purged = purge_archive(
            repo_path,
            older_than_days=older_than,
            dry_run=args.dry_run,
        )
        print(f"\n{'Would purge' if args.dry_run else 'Purged'}: {len(purged)} files")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
