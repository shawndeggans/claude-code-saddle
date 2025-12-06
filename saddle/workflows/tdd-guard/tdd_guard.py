#!/usr/bin/env python3
"""TDD Guard - Mechanical enforcement of test-driven development.

This module intercepts file write/edit operations and verifies that
corresponding test files exist before allowing implementation changes.
It enforces the "test first" principle by blocking operations when
tests are missing.

Exit Codes:
    0: Allow - proceed with operation
    1: Block - operation prevented, must create tests first
    2: Warn - operation allowed but tests incomplete
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import NamedTuple

import yaml


class GuardResult(NamedTuple):
    """Result of TDD guard check."""

    action: str  # "allow", "block", "warn"
    reason: str
    guidance: str
    exit_code: int  # 0=allow, 1=block, 2=warn


@dataclass
class TDDConfig:
    """TDD Guard configuration."""

    test_patterns: dict[str, str]
    excluded_paths: list[str]
    strict_mode: bool
    custom_rules: list[dict[str, str]]


DEFAULT_CONFIG = TDDConfig(
    test_patterns={
        "src/**/*.py": "tests/**/test_*.py",
        "project/src/**/*.py": "project/tests/**/test_*.py",
        "**/*.py": "tests/test_*.py",
        "src/**/*.js": "tests/**/*.test.js",
        "src/**/*.ts": "tests/**/*.spec.ts",
        "lib/**/*.ts": "__tests__/**/*.test.ts",
    },
    excluded_paths=[
        "**/migrations/**",
        "**/config/**",
        "**/__init__.py",
        "**/conftest.py",
        "**/setup.py",
        "**/settings.py",
        "**/manage.py",
        "**/.tdd-skip",
        "**/test_*.py",
        "**/tests/**",
        "**/*_test.py",
        "**/*.test.js",
        "**/*.spec.ts",
    ],
    strict_mode=False,
    custom_rules=[],
)


def load_config(config_path: Path | None = None) -> TDDConfig:
    """Load TDD Guard configuration from YAML file.

    Args:
        config_path: Path to config.yaml file.

    Returns:
        TDDConfig with loaded or default settings.
    """
    if config_path is None:
        # Look for config in default locations
        candidates = [
            Path.cwd() / "saddle" / "workflows" / "tdd-guard" / "config.yaml",
            Path.cwd() / ".tdd-guard.yaml",
            Path(__file__).parent / "config.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break

    if config_path is None or not config_path.exists():
        return DEFAULT_CONFIG

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError):
        return DEFAULT_CONFIG

    return TDDConfig(
        test_patterns=data.get("test_patterns", DEFAULT_CONFIG.test_patterns),
        excluded_paths=data.get("excluded_paths", DEFAULT_CONFIG.excluded_paths),
        strict_mode=data.get("strict_mode", DEFAULT_CONFIG.strict_mode),
        custom_rules=data.get("custom_rules", DEFAULT_CONFIG.custom_rules),
    )


def is_excluded(file_path: Path, config: TDDConfig) -> bool:
    """Check if file is excluded from TDD requirements.

    Args:
        file_path: Path to check.
        config: TDD configuration.

    Returns:
        True if file is excluded.
    """
    file_str = str(file_path)
    for pattern in config.excluded_paths:
        if fnmatch(file_str, pattern):
            return True
        # Also check just the filename
        if fnmatch(file_path.name, pattern.split("/")[-1]):
            return True
    return False


def is_test_file(file_path: Path) -> bool:
    """Check if a file is itself a test file.

    Args:
        file_path: Path to check.

    Returns:
        True if file is a test file.
    """
    name = file_path.name
    stem = file_path.stem

    # Python test patterns
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    if stem == "conftest":
        return True

    # JavaScript/TypeScript test patterns
    if name.endswith(".test.js") or name.endswith(".test.ts"):
        return True
    if name.endswith(".spec.js") or name.endswith(".spec.ts"):
        return True

    # In a tests directory
    if "tests" in file_path.parts or "__tests__" in file_path.parts:
        return True

    return False


def find_test_file(source_path: Path, config: TDDConfig) -> Path | None:
    """Find corresponding test file for a source file based on patterns.

    Args:
        source_path: Path to the source file.
        config: TDD configuration.

    Returns:
        Path to test file if found, None otherwise.
    """
    source_str = str(source_path)

    for source_pattern, test_pattern in config.test_patterns.items():
        if fnmatch(source_str, source_pattern) or fnmatch(source_path.name, source_pattern.split("/")[-1]):
            # Construct potential test file path
            stem = source_path.stem
            suffix = source_path.suffix

            # Python: foo.py -> test_foo.py
            if suffix == ".py":
                test_name = f"test_{stem}.py"
                # Look in various test locations
                candidates = [
                    source_path.parent.parent / "tests" / test_name,
                    source_path.parent / "tests" / test_name,
                    Path("tests") / test_name,
                    Path("project") / "tests" / test_name,
                ]

            # JavaScript: foo.js -> foo.test.js
            elif suffix in (".js", ".jsx", ".ts", ".tsx"):
                test_name = f"{stem}.test{suffix}"
                spec_name = f"{stem}.spec{suffix}"
                candidates = [
                    source_path.parent / "__tests__" / test_name,
                    source_path.parent / test_name,
                    Path("tests") / test_name,
                    source_path.parent / "__tests__" / spec_name,
                    source_path.parent / spec_name,
                ]
            else:
                continue

            for candidate in candidates:
                if candidate.exists():
                    return candidate

    return None


def extract_functions(file_path: Path) -> list[str]:
    """Extract function/method names from a source file.

    Uses Python AST for Python files, falls back to regex for others.

    Args:
        file_path: Path to the source file.

    Returns:
        List of function names found in the file.
    """
    if not file_path.exists():
        return []

    if file_path.suffix == ".py":
        return _extract_python_functions(file_path)
    elif file_path.suffix in (".js", ".ts", ".jsx", ".tsx"):
        return _extract_js_functions(file_path)

    return []


def _extract_python_functions(file_path: Path) -> list[str]:
    """Extract function names from Python file using AST."""
    import ast

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return []

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # Skip private functions for TDD check
            if not node.name.startswith("_"):
                functions.append(node.name)

    return functions


def _extract_js_functions(file_path: Path) -> list[str]:
    """Extract function names from JavaScript file using regex."""
    import re

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    functions = []

    # function declarations
    for match in re.finditer(r"function\s+(\w+)\s*\(", content):
        functions.append(match.group(1))

    # arrow functions assigned to const/let
    for match in re.finditer(r"(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(", content):
        functions.append(match.group(1))

    return functions


def extract_test_targets(test_path: Path) -> set[str]:
    """Extract function names that tests are targeting (heuristic-based).

    Looks for test_<name> patterns and function calls that suggest
    what's being tested.

    Args:
        test_path: Path to the test file.

    Returns:
        Set of function names that appear to be tested.
    """
    if not test_path.exists():
        return set()

    try:
        content = test_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return set()

    targets = set()

    if test_path.suffix == ".py":
        import re

        # test_<function_name> patterns
        for match in re.finditer(r"def test_(\w+)", content):
            # Extract the base name (test_foo_works -> foo)
            name = match.group(1)
            # Remove common suffixes
            for suffix in ("_works", "_returns", "_raises", "_success", "_failure"):
                if name.endswith(suffix):
                    name = name[: -len(suffix)]
                    break
            targets.add(name)

        # Direct function calls in tests
        for match in re.finditer(r"(\w+)\s*\(", content):
            targets.add(match.group(1))

    return targets


def check_function_coverage(
    source_path: Path, test_path: Path, function_name: str | None = None
) -> tuple[bool, list[str]]:
    """Check if test file has tests for functions in source file.

    Args:
        source_path: Path to the source file.
        test_path: Path to the test file.
        function_name: Specific function to check, or None for all.

    Returns:
        Tuple of (has_coverage, list of uncovered functions).
    """
    source_functions = extract_functions(source_path)
    test_targets = extract_test_targets(test_path)

    if function_name:
        source_functions = [f for f in source_functions if f == function_name]

    uncovered = []
    for func in source_functions:
        # Check if any test target matches this function
        is_covered = any(
            func.lower() in target.lower() or target.lower() in func.lower()
            for target in test_targets
        )
        if not is_covered:
            uncovered.append(func)

    return len(uncovered) == 0, uncovered


def run_guard(
    file_path: str,
    action: str,
    config_path: str | None = None,
    strict_mode: bool = False,
) -> GuardResult:
    """Main entry point for TDD Guard.

    Args:
        file_path: Path to file being written/edited.
        action: "write" or "edit".
        config_path: Optional path to config.yaml.
        strict_mode: If True, treat warnings as blocks.

    Returns:
        GuardResult with action, reason, guidance, and exit_code.
    """
    path = Path(file_path)
    config = load_config(Path(config_path) if config_path else None)

    if strict_mode:
        config.strict_mode = True

    # Always allow test files
    if is_test_file(path):
        return GuardResult(
            action="allow",
            reason="Test file - no restrictions",
            guidance="",
            exit_code=0,
        )

    # Check exclusions
    if is_excluded(path, config):
        return GuardResult(
            action="allow",
            reason=f"File excluded from TDD requirements: {path.name}",
            guidance="",
            exit_code=0,
        )

    # Check for corresponding test file
    test_file = find_test_file(path, config)

    if test_file is None:
        # No test file exists
        stem = path.stem
        test_name = f"test_{stem}.py" if path.suffix == ".py" else f"{stem}.test{path.suffix}"

        return GuardResult(
            action="block",
            reason=f"No test file found for {path.name}",
            guidance=f"TDD requires tests first. Create a test file (e.g., {test_name}) before implementing.",
            exit_code=1,
        )

    # Test file exists, check coverage
    has_coverage, uncovered = check_function_coverage(path, test_file)

    if not has_coverage and uncovered:
        warn_or_block = "block" if config.strict_mode else "warn"
        exit_code = 1 if config.strict_mode else 2

        return GuardResult(
            action=warn_or_block,
            reason=f"Missing test coverage for: {', '.join(uncovered[:3])}",
            guidance=f"Add tests for these functions in {test_file.name} before proceeding.",
            exit_code=exit_code,
        )

    return GuardResult(
        action="allow",
        reason=f"Test file exists: {test_file.name}",
        guidance="",
        exit_code=0,
    )


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TDD Guard - Enforce test-driven development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0 - Allow: Proceed with operation
  1 - Block: Operation prevented, create tests first
  2 - Warn: Operation allowed but tests are incomplete

Examples:
  tdd_guard.py src/auth.py write
  tdd_guard.py src/api/routes.py edit --strict
  tdd_guard.py src/models.py write --json
        """,
    )
    parser.add_argument("file_path", help="Path to file being modified")
    parser.add_argument(
        "action", choices=["write", "edit"], help="Type of operation"
    )
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument(
        "--strict", action="store_true", help="Block on warnings (strict mode)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output result as JSON"
    )

    args = parser.parse_args()

    result = run_guard(
        file_path=args.file_path,
        action=args.action,
        config_path=args.config,
        strict_mode=args.strict,
    )

    if args.json:
        output = {
            "action": result.action,
            "reason": result.reason,
            "guidance": result.guidance,
            "exit_code": result.exit_code,
        }
        print(json.dumps(output, indent=2))
    else:
        if result.action == "allow":
            print(f"[ALLOW] {result.reason}")
        elif result.action == "block":
            print(f"[BLOCK] {result.reason}")
            if result.guidance:
                print(f"  -> {result.guidance}")
        elif result.action == "warn":
            print(f"[WARN] {result.reason}")
            if result.guidance:
                print(f"  -> {result.guidance}")

    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
