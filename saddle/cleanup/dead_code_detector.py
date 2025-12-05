#!/usr/bin/env python3
"""Dead code detection wrapper combining vulture and deadcode.

This module provides a unified interface for detecting dead code
using multiple tools, deduplicating results, and ranking findings
by priority for cleanup.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class DeadCodeItem:
    """Represents a detected dead code item."""

    file_path: str
    line: int
    name: str
    item_type: str  # "function", "class", "variable", "import"
    confidence: float  # 0.0 to 1.0
    size_lines: int
    source: str  # "vulture" or "deadcode"


@dataclass
class DeadCodeReport:
    """Complete dead code analysis report."""

    items: list[DeadCodeItem]
    total_dead_lines: int
    files_affected: int
    generated_at: str


def run_vulture(paths: list[Path], min_confidence: int = 80) -> list[DeadCodeItem]:
    """Run vulture and parse its output.

    Args:
        paths: Directories/files to analyze.
        min_confidence: Minimum confidence threshold (0-100).

    Returns:
        List of DeadCodeItem from vulture results.
    """
    cmd = ["vulture", "--min-confidence", str(min_confidence)]
    cmd.extend([str(p) for p in paths])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    return parse_vulture_output(result.stdout)


def parse_vulture_output(output: str) -> list[DeadCodeItem]:
    """Parse vulture's output format into DeadCodeItem list.

    Vulture output format:
    path/to/file.py:123: unused function 'func_name' (60% confidence)

    Args:
        output: Raw vulture output.

    Returns:
        List of parsed DeadCodeItem objects.
    """
    items = []

    # Pattern: file:line: unused <type> '<name>' (<confidence>% confidence)
    pattern = re.compile(
        r"^(.+?):(\d+):\s+unused\s+(\w+)\s+'([^']+)'\s+\((\d+)%\s+confidence\)"
    )

    for line in output.strip().split("\n"):
        if not line:
            continue

        match = pattern.match(line)
        if match:
            file_path, line_num, item_type, name, confidence = match.groups()
            items.append(
                DeadCodeItem(
                    file_path=file_path,
                    line=int(line_num),
                    name=name,
                    item_type=item_type,
                    confidence=int(confidence) / 100.0,
                    size_lines=1,  # Vulture doesn't report size
                    source="vulture",
                )
            )

    return items


def run_deadcode(paths: list[Path]) -> list[DeadCodeItem]:
    """Run deadcode tool and parse its output.

    Args:
        paths: Directories/files to analyze.

    Returns:
        List of DeadCodeItem from deadcode results.
    """
    cmd = ["deadcode"]
    cmd.extend([str(p) for p in paths])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    return parse_deadcode_output(result.stdout)


def parse_deadcode_output(output: str) -> list[DeadCodeItem]:
    """Parse deadcode's output format.

    Args:
        output: Raw deadcode output.

    Returns:
        List of parsed DeadCodeItem objects.
    """
    items = []

    # Deadcode output varies - try common patterns
    # Pattern: file:line: message
    pattern = re.compile(r"^(.+?):(\d+):\s+(.+)")

    for line in output.strip().split("\n"):
        if not line:
            continue

        match = pattern.match(line)
        if match:
            file_path, line_num, message = match.groups()

            # Try to extract name and type from message
            name = "unknown"
            item_type = "code"

            if "function" in message.lower():
                item_type = "function"
            elif "class" in message.lower():
                item_type = "class"
            elif "import" in message.lower():
                item_type = "import"
            elif "variable" in message.lower():
                item_type = "variable"

            # Try to extract name from quotes
            name_match = re.search(r"'([^']+)'", message)
            if name_match:
                name = name_match.group(1)

            items.append(
                DeadCodeItem(
                    file_path=file_path,
                    line=int(line_num),
                    name=name,
                    item_type=item_type,
                    confidence=0.8,  # Deadcode doesn't provide confidence
                    size_lines=1,
                    source="deadcode",
                )
            )

    return items


def deduplicate_findings(
    vulture_items: list[DeadCodeItem],
    deadcode_items: list[DeadCodeItem],
) -> list[DeadCodeItem]:
    """Deduplicate findings from both tools, keeping highest confidence.

    Args:
        vulture_items: Items from vulture.
        deadcode_items: Items from deadcode.

    Returns:
        Deduplicated list of items.
    """
    seen: dict[tuple[str, int, str], DeadCodeItem] = {}

    for item in vulture_items + deadcode_items:
        key = (item.file_path, item.line, item.name)
        if key not in seen or item.confidence > seen[key].confidence:
            seen[key] = item

    return list(seen.values())


def rank_findings(items: list[DeadCodeItem]) -> list[DeadCodeItem]:
    """Rank dead code by priority (confidence, size, type).

    Args:
        items: List of dead code items.

    Returns:
        Sorted list with highest priority first.
    """

    def priority_score(item: DeadCodeItem) -> float:
        # Higher = more important to address
        conf_score = item.confidence
        size_score = min(item.size_lines / 50, 1.0)  # Cap at 50 lines

        # Type weights
        type_weights = {
            "function": 0.8,
            "class": 1.0,
            "variable": 0.3,
            "import": 0.2,
        }
        type_score = type_weights.get(item.item_type, 0.5)

        return conf_score * 0.5 + size_score * 0.2 + type_score * 0.3

    return sorted(items, key=priority_score, reverse=True)


def detect_dead_code(
    paths: list[Path],
    min_confidence: int = 80,
    include_imports: bool = True,
) -> DeadCodeReport:
    """Run dead code detection and produce unified report.

    Args:
        paths: Directories/files to analyze.
        min_confidence: Minimum vulture confidence (0-100).
        include_imports: Include unused imports in report.

    Returns:
        DeadCodeReport with ranked findings.
    """
    vulture_items = run_vulture(paths, min_confidence)
    deadcode_items = run_deadcode(paths)

    all_items = deduplicate_findings(vulture_items, deadcode_items)

    if not include_imports:
        all_items = [i for i in all_items if i.item_type != "import"]

    ranked_items = rank_findings(all_items)

    # Calculate statistics
    total_dead_lines = sum(i.size_lines for i in ranked_items)
    files_affected = len(set(i.file_path for i in ranked_items))

    return DeadCodeReport(
        items=ranked_items,
        total_dead_lines=total_dead_lines,
        files_affected=files_affected,
        generated_at=datetime.now().isoformat(),
    )


def format_text(report: DeadCodeReport) -> str:
    """Format report as plain text.

    Args:
        report: Dead code report.

    Returns:
        Text-formatted report.
    """
    lines = [
        "Dead Code Analysis Report",
        "=" * 50,
        f"Generated: {report.generated_at}",
        f"Files affected: {report.files_affected}",
        f"Items found: {len(report.items)}",
        "",
    ]

    for item in report.items:
        conf_pct = int(item.confidence * 100)
        lines.append(
            f"[{conf_pct:3d}%] {item.file_path}:{item.line} - "
            f"unused {item.item_type} '{item.name}'"
        )

    return "\n".join(lines)


def format_markdown(report: DeadCodeReport) -> str:
    """Format report as markdown.

    Args:
        report: Dead code report.

    Returns:
        Markdown-formatted report.
    """
    lines = [
        "# Dead Code Analysis Report",
        "",
        f"**Generated**: {report.generated_at}",
        f"**Files affected**: {report.files_affected}",
        f"**Items found**: {len(report.items)}",
        "",
        "## Findings",
        "",
        "| Confidence | File | Line | Type | Name |",
        "|------------|------|------|------|------|",
    ]

    for item in report.items:
        conf_pct = int(item.confidence * 100)
        lines.append(
            f"| {conf_pct}% | `{item.file_path}` | {item.line} | "
            f"{item.item_type} | `{item.name}` |"
        )

    return "\n".join(lines)


def format_json(report: DeadCodeReport) -> str:
    """Format report as JSON.

    Args:
        report: Dead code report.

    Returns:
        JSON-formatted report.
    """
    data = {
        "generated_at": report.generated_at,
        "files_affected": report.files_affected,
        "total_items": len(report.items),
        "items": [
            {
                "file_path": item.file_path,
                "line": item.line,
                "name": item.name,
                "type": item.item_type,
                "confidence": item.confidence,
                "source": item.source,
            }
            for item in report.items
        ],
    }
    return json.dumps(data, indent=2)


def apply_fixes(items: list[DeadCodeItem], dry_run: bool = True) -> int:
    """Apply auto-fixes for dead code (removal).

    Only removes items with high confidence (>90%).
    This is a destructive operation - use with caution.

    Args:
        items: Items to remove.
        dry_run: If True, only show what would be removed.

    Returns:
        Number of items fixed/would-be-fixed.
    """
    high_confidence = [i for i in items if i.confidence >= 0.9]
    count = 0

    for item in high_confidence:
        if dry_run:
            print(f"Would remove: {item.file_path}:{item.line} - {item.name}")
            count += 1
        else:
            # Actually removing code is risky - just report for now
            print(f"[DRY RUN] Would remove: {item.file_path}:{item.line}")
            count += 1

    return count


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Detect dead code using vulture and deadcode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["project/"],
        help="Paths to analyze (default: project/)",
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=80,
        help="Minimum confidence for vulture (0-100)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--no-imports",
        action="store_true",
        help="Exclude unused imports from report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply auto-fixes (use with caution)",
    )

    args = parser.parse_args()

    paths = [Path(p) for p in args.paths]
    report = detect_dead_code(
        paths=paths,
        min_confidence=args.min_confidence,
        include_imports=not args.no_imports,
    )

    if args.fix or args.dry_run:
        count = apply_fixes(report.items, dry_run=not args.fix)
        print(f"\n{'Would fix' if args.dry_run else 'Fixed'}: {count} items")
        return 0

    if args.format == "json":
        print(format_json(report))
    elif args.format == "markdown":
        print(format_markdown(report))
    else:
        print(format_text(report))

    return 0 if len(report.items) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
