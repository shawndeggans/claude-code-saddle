#!/usr/bin/env python3
"""Documentation verification system for pre-commit enforcement.

This module checks that code changes have corresponding documentation
updates. It verifies docstrings for new modules/functions and checks
for missing CHANGELOG entries.

Exit Codes:
    0: Pass - all documentation requirements met
    1: Fail - missing documentation found
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocIssue:
    """Represents a documentation issue."""

    file_path: Path
    issue_type: str  # "missing_module_docstring", "missing_function_docstring", etc.
    location: str  # line number or function name
    suggestion: str
    severity: str = "error"  # "error" or "warning"


@dataclass
class VerificationResult:
    """Result of documentation verification."""

    passed: bool
    issues: list[DocIssue] = field(default_factory=list)
    summary: str = ""


def get_staged_files() -> list[Path]:
    """Get list of staged Python files from git.

    Returns:
        List of Path objects for staged Python files.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        files = [
            Path(f)
            for f in result.stdout.strip().split("\n")
            if f and f.endswith(".py")
        ]
        return [f for f in files if f.exists()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def get_changed_files(base_ref: str = "HEAD~1") -> list[Path]:
    """Get list of changed Python files since base ref.

    Args:
        base_ref: Git reference to compare against.

    Returns:
        List of changed Python file paths.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        files = [
            Path(f)
            for f in result.stdout.strip().split("\n")
            if f and f.endswith(".py")
        ]
        return [f for f in files if f.exists()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def parse_python_file(file_path: Path) -> ast.Module | None:
    """Parse Python file into AST, handling errors gracefully.

    Args:
        file_path: Path to the Python file.

    Returns:
        Parsed AST module, or None on error.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        return ast.parse(content, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
        return None


def is_public(name: str) -> bool:
    """Determine if a name represents a public API.

    Args:
        name: The function/class name.

    Returns:
        True if the name is public (doesn't start with _).
    """
    return not name.startswith("_")


def check_module_docstring(file_path: Path) -> DocIssue | None:
    """Check if module has a docstring.

    Args:
        file_path: Path to the Python file.

    Returns:
        DocIssue if module lacks docstring, None otherwise.
    """
    tree = parse_python_file(file_path)
    if tree is None:
        return None

    docstring = ast.get_docstring(tree)
    if docstring is None:
        return DocIssue(
            file_path=file_path,
            issue_type="missing_module_docstring",
            location="module",
            suggestion="Add a module-level docstring explaining the module's purpose.",
            severity="warning",
        )
    return None


def check_function_docstrings(file_path: Path) -> list[DocIssue]:
    """Check all public functions have docstrings.

    Args:
        file_path: Path to the Python file.

    Returns:
        List of DocIssue for functions missing docstrings.
    """
    tree = parse_python_file(file_path)
    if tree is None:
        return []

    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if not is_public(node.name):
                continue

            # Skip if it's a method in a class (check parent)
            # This simplified version checks all functions
            docstring = ast.get_docstring(node)
            if docstring is None:
                issues.append(
                    DocIssue(
                        file_path=file_path,
                        issue_type="missing_function_docstring",
                        location=f"line {node.lineno}: {node.name}()",
                        suggestion=f"Add a docstring to function '{node.name}'.",
                        severity="warning",
                    )
                )

    return issues


def check_class_docstrings(file_path: Path) -> list[DocIssue]:
    """Check all public classes have docstrings.

    Args:
        file_path: Path to the Python file.

    Returns:
        List of DocIssue for classes missing docstrings.
    """
    tree = parse_python_file(file_path)
    if tree is None:
        return []

    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not is_public(node.name):
                continue

            docstring = ast.get_docstring(node)
            if docstring is None:
                issues.append(
                    DocIssue(
                        file_path=file_path,
                        issue_type="missing_class_docstring",
                        location=f"line {node.lineno}: class {node.name}",
                        suggestion=f"Add a docstring to class '{node.name}'.",
                        severity="warning",
                    )
                )

    return issues


def detect_api_changes(file_path: Path, base_ref: str = "HEAD") -> bool:
    """Detect if file contains API endpoint changes requiring doc updates.

    Looks for common API decorators/patterns that suggest REST endpoints.

    Args:
        file_path: Path to the Python file.
        base_ref: Git reference to compare against.

    Returns:
        True if API changes detected.
    """
    tree = parse_python_file(file_path)
    if tree is None:
        return False

    api_decorators = {
        "route",
        "get",
        "post",
        "put",
        "delete",
        "patch",
        "api_view",
        "app.route",
        "router.get",
        "router.post",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                dec_name = ""
                if isinstance(decorator, ast.Name):
                    dec_name = decorator.id
                elif isinstance(decorator, ast.Attribute):
                    dec_name = decorator.attr
                elif isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Name):
                        dec_name = decorator.func.id
                    elif isinstance(decorator.func, ast.Attribute):
                        dec_name = decorator.func.attr

                if dec_name.lower() in api_decorators:
                    return True

    return False


def check_changelog_entry(file_path: Path) -> DocIssue | None:
    """Check if significant changes have corresponding CHANGELOG entry.

    This is a heuristic check - it looks for CHANGELOG.md in the repo
    and checks if it's been modified recently.

    Args:
        file_path: Path being checked.

    Returns:
        DocIssue if CHANGELOG update might be needed, None otherwise.
    """
    # Find CHANGELOG.md
    changelog_candidates = [
        Path("CHANGELOG.md"),
        Path("project/CHANGELOG.md"),
        Path("docs/CHANGELOG.md"),
    ]

    changelog_path = None
    for candidate in changelog_candidates:
        if candidate.exists():
            changelog_path = candidate
            break

    if changelog_path is None:
        # No CHANGELOG to check
        return None

    # Check if CHANGELOG was modified in staged changes
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        staged_files = result.stdout.strip().split("\n") if result.returncode == 0 else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        staged_files = []

    if str(changelog_path) in staged_files:
        # CHANGELOG was updated
        return None

    # Check if this looks like a feature addition
    if detect_api_changes(file_path):
        return DocIssue(
            file_path=file_path,
            issue_type="missing_changelog_entry",
            location="CHANGELOG.md",
            suggestion="API changes detected. Consider adding a CHANGELOG entry.",
            severity="warning",
        )

    return None


def verify_documentation(
    check_staged: bool = True,
    files: list[Path] | None = None,
    strict: bool = False,
) -> VerificationResult:
    """Main verification entry point.

    Args:
        check_staged: If True, check git staged files.
        files: Explicit list of files to check.
        strict: If True, treat warnings as errors.

    Returns:
        VerificationResult with pass/fail status and issues.
    """
    if files:
        files_to_check = files
    elif check_staged:
        files_to_check = get_staged_files()
    else:
        files_to_check = []

    all_issues: list[DocIssue] = []

    for file_path in files_to_check:
        if not file_path.exists():
            continue

        # Skip test files
        if "test" in file_path.name or str(file_path).startswith("tests"):
            continue

        # Check module docstring
        module_issue = check_module_docstring(file_path)
        if module_issue:
            all_issues.append(module_issue)

        # Check function docstrings
        func_issues = check_function_docstrings(file_path)
        all_issues.extend(func_issues)

        # Check class docstrings
        class_issues = check_class_docstrings(file_path)
        all_issues.extend(class_issues)

        # Check for CHANGELOG needs
        changelog_issue = check_changelog_entry(file_path)
        if changelog_issue:
            all_issues.append(changelog_issue)

    # Determine pass/fail
    if strict:
        passed = len(all_issues) == 0
    else:
        errors = [i for i in all_issues if i.severity == "error"]
        passed = len(errors) == 0

    summary = f"Checked {len(files_to_check)} files, found {len(all_issues)} issues"

    return VerificationResult(
        passed=passed,
        issues=all_issues,
        summary=summary,
    )


def format_checklist(issues: list[DocIssue]) -> str:
    """Format issues as actionable markdown checklist.

    Args:
        issues: List of documentation issues.

    Returns:
        Markdown-formatted checklist.
    """
    if not issues:
        return "No documentation issues found."

    lines = ["Documentation Issues Found:", ""]

    for issue in issues:
        severity_marker = "[!]" if issue.severity == "error" else "[ ]"
        lines.append(
            f"- {severity_marker} {issue.file_path}:{issue.location} - {issue.suggestion}"
        )

    return "\n".join(lines)


def format_text(issues: list[DocIssue]) -> str:
    """Format issues as plain text.

    Args:
        issues: List of documentation issues.

    Returns:
        Text-formatted issue list.
    """
    if not issues:
        return "No documentation issues found."

    lines = []
    for issue in issues:
        prefix = "ERROR" if issue.severity == "error" else "WARN"
        lines.append(f"[{prefix}] {issue.file_path}:{issue.location}")
        lines.append(f"  {issue.suggestion}")

    return "\n".join(lines)


def format_json(result: VerificationResult) -> str:
    """Format result as JSON.

    Args:
        result: Verification result.

    Returns:
        JSON-formatted result.
    """
    import json

    data = {
        "passed": result.passed,
        "summary": result.summary,
        "issues": [
            {
                "file_path": str(issue.file_path),
                "issue_type": issue.issue_type,
                "location": issue.location,
                "suggestion": issue.suggestion,
                "severity": issue.severity,
            }
            for issue in result.issues
        ],
    }
    return json.dumps(data, indent=2)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Verify documentation completeness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  doc_verify.py --check-staged         # Check staged files
  doc_verify.py --files src/module.py  # Check specific file
  doc_verify.py --strict               # Treat warnings as errors
        """,
    )
    parser.add_argument(
        "--check-staged",
        action="store_true",
        help="Check git staged files",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        help="Specific files to check",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "checklist"],
        default="checklist",
        help="Output format",
    )

    args = parser.parse_args()

    result = verify_documentation(
        check_staged=args.check_staged,
        files=args.files,
        strict=args.strict,
    )

    if args.format == "json":
        print(format_json(result))
    elif args.format == "checklist":
        print(format_checklist(result.issues))
    else:
        print(format_text(result.issues))

    print()
    print(result.summary)

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
