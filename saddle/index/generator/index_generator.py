#!/usr/bin/env python3
"""Codebase auto-indexing system for Claude Code Saddle.

Generates structural indexes of codebases including:
- codebase-index.json: File/function/class map
- dependency-graph.json: Import relationships
- stale-files.json: Candidates for archival
- CODEBASE.md: Human-readable summary
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .parsers import generic_parser, js_parser, python_parser


@dataclass
class FileIndex:
    """Index entry for a single file."""

    path: str
    language: str
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    last_modified: str = ""
    lines_of_code: int = 0


@dataclass
class IndexResult:
    """Complete index generation result."""

    codebase_index: dict[str, dict[str, Any]]
    dependency_graph: dict[str, list[str]]
    stale_files: dict[str, dict[str, Any]]
    statistics: dict[str, int]


# File patterns to exclude from indexing
DEFAULT_EXCLUDE_PATTERNS = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "*.egg-info",
    "dist",
    "build",
    ".tox",
    ".coverage",
    "htmlcov",
    ".archive",
]

# Supported file extensions by parser
PYTHON_EXTENSIONS = {".py"}
JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}


def get_changed_files_since(ref: str = "HEAD~1", project_path: Path | None = None) -> list[Path]:
    """Get files changed since given git ref for incremental updates.

    Args:
        ref: Git reference to compare against.
        project_path: Path to run git command in.

    Returns:
        List of changed file paths.
    """
    cwd = project_path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        files = [Path(f) for f in result.stdout.strip().split("\n") if f]
        return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def detect_language(file_path: Path) -> str | None:
    """Detect programming language from file extension.

    Args:
        file_path: Path to the file.

    Returns:
        Language name, or None if not supported.
    """
    ext = file_path.suffix.lower()
    if ext in PYTHON_EXTENSIONS:
        return "python"
    if ext in JS_EXTENSIONS:
        return "javascript"
    if generic_parser.get_language_for_extension(ext):
        return generic_parser.get_language_for_extension(ext)
    return None


def should_exclude(path: Path, exclude_patterns: list[str]) -> bool:
    """Check if path should be excluded from indexing.

    Args:
        path: Path to check.
        exclude_patterns: List of patterns to exclude.

    Returns:
        True if path should be excluded.
    """
    path_str = str(path)
    for pattern in exclude_patterns:
        if pattern in path_str:
            return True
    return False


def walk_project(
    project_path: Path, exclude_patterns: list[str] | None = None
) -> list[Path]:
    """Walk project directory, respecting exclusions.

    Args:
        project_path: Root directory to walk.
        exclude_patterns: Patterns to exclude.

    Returns:
        List of source file paths.
    """
    if exclude_patterns is None:
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS

    files = []
    if not project_path.exists():
        return files

    for path in project_path.rglob("*"):
        if not path.is_file():
            continue
        if should_exclude(path, exclude_patterns):
            continue
        if detect_language(path) is None:
            continue
        files.append(path)

    return sorted(files, key=lambda p: str(p))


def get_file_last_modified(file_path: Path) -> str:
    """Get last modification timestamp for file.

    Args:
        file_path: Path to the file.

    Returns:
        ISO format timestamp string.
    """
    try:
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).isoformat()
    except (FileNotFoundError, PermissionError):
        return ""


def parse_file(file_path: Path) -> FileIndex | None:
    """Parse a source file and extract structural information.

    Args:
        file_path: Path to the source file.

    Returns:
        FileIndex with extracted information, or None if parsing fails.
    """
    language = detect_language(file_path)
    if language is None:
        return None

    if language == "python":
        result = python_parser.parse_file(file_path)
        if result is None:
            return None
        return FileIndex(
            path=str(file_path),
            language=language,
            functions=result.functions,
            classes=result.classes,
            imports=result.imports,
            decorators=result.decorators,
            docstring=result.docstring,
            last_modified=get_file_last_modified(file_path),
            lines_of_code=python_parser.count_lines_of_code(file_path),
        )

    if language == "javascript":
        result = js_parser.parse_file(file_path)
        if result is None:
            return None
        return FileIndex(
            path=str(file_path),
            language=language,
            functions=result.functions,
            classes=result.classes,
            imports=result.imports,
            last_modified=get_file_last_modified(file_path),
            lines_of_code=js_parser.count_lines_of_code(file_path),
        )

    # Use generic parser for other languages
    result = generic_parser.parse_file(file_path)
    if result is None:
        return None
    return FileIndex(
        path=str(file_path),
        language=result.language,
        functions=result.functions,
        classes=result.classes,
        last_modified=get_file_last_modified(file_path),
        lines_of_code=generic_parser.count_lines_of_code(file_path),
    )


def generate_codebase_index(
    project_path: Path,
    incremental: bool = False,
    existing_index: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Generate or update codebase-index.json content.

    Args:
        project_path: Root directory of the project.
        incremental: If True, only reindex changed files.
        existing_index: Existing index for incremental updates.

    Returns:
        Dictionary mapping file paths to their index entries.
    """
    index: dict[str, dict[str, Any]] = existing_index or {}

    if incremental and existing_index:
        # Only process changed files
        changed_files = get_changed_files_since("HEAD~1", project_path)
        files_to_process = [project_path / f for f in changed_files if (project_path / f).exists()]
    else:
        # Process all files
        files_to_process = walk_project(project_path)

    for file_path in files_to_process:
        file_index = parse_file(file_path)
        if file_index is not None:
            # Use relative path as key
            try:
                rel_path = str(file_path.relative_to(project_path))
            except ValueError:
                rel_path = str(file_path)
            index[rel_path] = asdict(file_index)

    return index


def generate_dependency_graph(
    codebase_index: dict[str, dict[str, Any]], project_path: Path
) -> dict[str, list[str]]:
    """Build module dependency graph from imports.

    Args:
        codebase_index: The generated codebase index.
        project_path: Root directory of the project.

    Returns:
        Dictionary mapping module names to their dependencies.
    """
    graph: dict[str, list[str]] = {}

    for file_path, file_info in codebase_index.items():
        # Convert file path to module name (Python style)
        module_name = (
            file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        )

        imports = file_info.get("imports", [])
        # Filter to likely internal imports
        internal_imports = []
        for imp in imports:
            # Skip standard library and common external packages
            if imp.startswith(("os", "sys", "re", "json", "typing", "pathlib")):
                continue
            if imp.startswith(("numpy", "pandas", "requests", "flask", "django")):
                continue
            internal_imports.append(imp)

        if internal_imports:
            graph[module_name] = internal_imports

    return graph


def generate_stale_files(
    codebase_index: dict[str, dict[str, Any]],
    dependency_graph: dict[str, list[str]],
    project_path: Path,
    staleness_threshold_days: int = 180,
) -> dict[str, dict[str, Any]]:
    """Identify potentially stale files based on age and usage.

    Args:
        codebase_index: The generated codebase index.
        dependency_graph: The module dependency graph.
        project_path: Root directory of the project.
        staleness_threshold_days: Days without modification to consider stale.

    Returns:
        Dictionary of stale file information.
    """
    stale_files: dict[str, dict[str, Any]] = {}

    # Build set of all referenced modules
    referenced_modules: set[str] = set()
    for deps in dependency_graph.values():
        referenced_modules.update(deps)

    now = datetime.now()

    for file_path, file_info in codebase_index.items():
        last_modified_str = file_info.get("last_modified", "")
        if not last_modified_str:
            continue

        try:
            last_modified = datetime.fromisoformat(last_modified_str)
            days_since_modified = (now - last_modified).days
        except ValueError:
            continue

        if days_since_modified < staleness_threshold_days:
            continue

        # Check if file is referenced
        module_name = file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        is_referenced = any(
            module_name in ref or ref in module_name for ref in referenced_modules
        )

        if not is_referenced:
            staleness_score = min(1.0, days_since_modified / (staleness_threshold_days * 2))
            stale_files[file_path] = {
                "last_modified": last_modified_str,
                "days_since_modified": days_since_modified,
                "staleness_score": round(staleness_score, 2),
                "reasons": ["not_referenced", "old"],
            }

    return stale_files


def generate_codebase_md(
    index_result: IndexResult, project_path: Path, max_lines: int = 500
) -> str:
    """Generate human-readable CODEBASE.md summary.

    Args:
        index_result: The complete index result.
        project_path: Root directory of the project.
        max_lines: Maximum lines for the output.

    Returns:
        Markdown content for CODEBASE.md.
    """
    lines = ["# Codebase Index", ""]
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")

    # Statistics
    stats = index_result.statistics
    lines.append("## Statistics")
    lines.append("")
    lines.append(f"- **Total files**: {stats.get('total_files', 0)}")
    lines.append(f"- **Total lines of code**: {stats.get('total_loc', 0)}")
    lines.append(f"- **Total functions**: {stats.get('total_functions', 0)}")
    lines.append(f"- **Total classes**: {stats.get('total_classes', 0)}")
    lines.append("")

    # Directory structure (simplified)
    lines.append("## Structure")
    lines.append("")
    lines.append("```")

    # Group files by directory
    dirs: dict[str, list[str]] = {}
    for file_path in sorted(index_result.codebase_index.keys()):
        parts = Path(file_path).parts
        if len(parts) > 1:
            dir_name = parts[0]
            if dir_name not in dirs:
                dirs[dir_name] = []
            dirs[dir_name].append(file_path)
        else:
            if "." not in dirs:
                dirs["."] = []
            dirs["."].append(file_path)

    for dir_name in sorted(dirs.keys()):
        if dir_name == ".":
            for f in dirs[dir_name][:5]:
                lines.append(f"  {f}")
        else:
            lines.append(f"{dir_name}/")
            for f in dirs[dir_name][:5]:
                rel = str(Path(f).relative_to(dir_name)) if dir_name != "." else f
                lines.append(f"  {rel}")
            if len(dirs[dir_name]) > 5:
                lines.append(f"  ... and {len(dirs[dir_name]) - 5} more files")

    lines.append("```")
    lines.append("")

    # Key entry points (files with main, app, or no underscores)
    lines.append("## Key Entry Points")
    lines.append("")
    for file_path, file_info in sorted(index_result.codebase_index.items()):
        file_name = Path(file_path).stem
        if file_name in ("main", "app", "cli", "server", "index"):
            funcs = file_info.get("functions", [])[:3]
            lines.append(f"- `{file_path}`: {', '.join(funcs) if funcs else 'entry point'}")

    lines.append("")

    # Key modules (by function/class count)
    lines.append("## Key Modules")
    lines.append("")
    sorted_by_content = sorted(
        index_result.codebase_index.items(),
        key=lambda x: len(x[1].get("functions", [])) + len(x[1].get("classes", [])),
        reverse=True,
    )
    for file_path, file_info in sorted_by_content[:10]:
        funcs = file_info.get("functions", [])
        classes = file_info.get("classes", [])
        desc_parts = []
        if classes:
            desc_parts.append(f"classes: {', '.join(classes[:3])}")
        if funcs:
            desc_parts.append(f"functions: {', '.join(funcs[:3])}")
        if desc_parts:
            lines.append(f"- `{file_path}`: {'; '.join(desc_parts)}")

    lines.append("")

    # Recently modified
    lines.append("## Recently Modified")
    lines.append("")
    recent = sorted(
        [
            (f, info)
            for f, info in index_result.codebase_index.items()
            if info.get("last_modified")
        ],
        key=lambda x: x[1].get("last_modified", ""),
        reverse=True,
    )[:5]
    for file_path, file_info in recent:
        mod_date = file_info.get("last_modified", "")[:10]
        lines.append(f"- `{file_path}` ({mod_date})")

    lines.append("")

    # Stale files
    if index_result.stale_files:
        lines.append("## Potentially Stale")
        lines.append("")
        for file_path, stale_info in list(index_result.stale_files.items())[:5]:
            score = stale_info.get("staleness_score", 0)
            days = stale_info.get("days_since_modified", 0)
            lines.append(f"- `{file_path}` (score: {score}, {days} days old)")
        lines.append("")

    # Truncate if needed
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("")
        lines.append("*Index truncated for brevity*")

    return "\n".join(lines)


def write_outputs(
    index_result: IndexResult,
    output_dir: Path,
    codebase_md: str,
) -> None:
    """Write all index files to output directory.

    Args:
        index_result: The complete index result.
        output_dir: Directory to write outputs to.
        codebase_md: Content for CODEBASE.md.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON files
    (output_dir / "codebase-index.json").write_text(
        json.dumps(index_result.codebase_index, indent=2)
    )
    (output_dir / "dependency-graph.json").write_text(
        json.dumps(index_result.dependency_graph, indent=2)
    )
    (output_dir / "stale-files.json").write_text(
        json.dumps(index_result.stale_files, indent=2)
    )

    # Write markdown
    (output_dir / "CODEBASE.md").write_text(codebase_md)


def run_indexer(
    project_path: Path | None = None,
    output_dir: Path | None = None,
    incremental: bool = True,
    verbose: bool = False,
) -> IndexResult:
    """Main entry point for index generation.

    Args:
        project_path: Path to project/ directory (default: ./project).
        output_dir: Path to output directory (default: ./saddle/index).
        incremental: If True, only reindex changed files.
        verbose: If True, print progress information.

    Returns:
        IndexResult with all generated data.
    """
    # Resolve paths
    cwd = Path.cwd()
    if project_path is None:
        project_path = cwd / "project"
    if output_dir is None:
        output_dir = cwd / "saddle" / "index"

    if verbose:
        print(f"Indexing: {project_path}")
        print(f"Output: {output_dir}")

    # Load existing index for incremental updates
    existing_index: dict[str, Any] | None = None
    if incremental:
        index_file = output_dir / "codebase-index.json"
        if index_file.exists():
            try:
                existing_index = json.loads(index_file.read_text())
            except json.JSONDecodeError:
                existing_index = None

    # Generate indexes
    codebase_index = generate_codebase_index(project_path, incremental, existing_index)
    dependency_graph = generate_dependency_graph(codebase_index, project_path)
    stale_files = generate_stale_files(codebase_index, dependency_graph, project_path)

    # Calculate statistics
    total_loc = sum(f.get("lines_of_code", 0) for f in codebase_index.values())
    total_functions = sum(len(f.get("functions", [])) for f in codebase_index.values())
    total_classes = sum(len(f.get("classes", [])) for f in codebase_index.values())

    statistics = {
        "total_files": len(codebase_index),
        "total_loc": total_loc,
        "total_functions": total_functions,
        "total_classes": total_classes,
    }

    result = IndexResult(
        codebase_index=codebase_index,
        dependency_graph=dependency_graph,
        stale_files=stale_files,
        statistics=statistics,
    )

    # Generate and write outputs
    codebase_md = generate_codebase_md(result, project_path)
    write_outputs(result, output_dir, codebase_md)

    if verbose:
        print(f"Indexed {statistics['total_files']} files")
        print(f"Found {statistics['total_functions']} functions")
        print(f"Found {statistics['total_classes']} classes")
        print(f"Identified {len(stale_files)} stale files")

    return result


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate codebase index for Claude Code Saddle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python index_generator.py                    # Incremental update
  python index_generator.py --full             # Full rebuild
  python index_generator.py --project ../app   # Custom project path
        """,
    )
    parser.add_argument("--project", type=Path, help="Path to project directory")
    parser.add_argument("--output", type=Path, help="Path to output directory")
    parser.add_argument(
        "--full", action="store_true", help="Force full rebuild (ignore incremental)"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        default=True,
        help="Only reindex changed files (default)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    incremental = not args.full

    try:
        run_indexer(
            project_path=args.project,
            output_dir=args.output,
            incremental=incremental,
            verbose=args.verbose,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
