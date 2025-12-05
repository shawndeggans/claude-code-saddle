#!/usr/bin/env python3
"""Python-specific AST parser for codebase indexing.

Uses Python's built-in ast module to extract structural information
from Python source files, including functions, classes, imports,
decorators, and docstrings.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class PythonParseResult:
    """Result of parsing a Python file."""

    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    class_methods: dict[str, list[str]] = field(default_factory=dict)
    async_functions: list[str] = field(default_factory=list)


def parse_file(file_path: Path) -> PythonParseResult | None:
    """Parse a Python file and extract structural information.

    Args:
        file_path: Path to the Python file to parse.

    Returns:
        PythonParseResult with extracted information, or None if parsing fails.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
        return None

    return PythonParseResult(
        functions=extract_functions(tree),
        classes=[name for name, _ in extract_classes(tree)],
        imports=extract_imports(tree),
        decorators=extract_decorators(tree),
        docstring=get_module_docstring(tree),
        class_methods={name: methods for name, methods in extract_classes(tree)},
        async_functions=extract_async_functions(tree),
    )


def extract_imports(tree: ast.Module) -> list[str]:
    """Extract all import statements from AST.

    Args:
        tree: Parsed AST module.

    Returns:
        List of imported module names.
    """
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    imports.append(f"{module}.*")
                else:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
    return imports


def extract_functions(tree: ast.Module) -> list[str]:
    """Extract top-level function definitions.

    Args:
        tree: Parsed AST module.

    Returns:
        List of function names defined at module level.
    """
    return [
        node.name
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def extract_async_functions(tree: ast.Module) -> list[str]:
    """Extract async function definitions.

    Args:
        tree: Parsed AST module.

    Returns:
        List of async function names.
    """
    return [
        node.name
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, ast.AsyncFunctionDef)
    ]


def extract_classes(tree: ast.Module) -> list[tuple[str, list[str]]]:
    """Extract class definitions with their methods.

    Args:
        tree: Parsed AST module.

    Returns:
        List of tuples (class_name, [method_names]).
    """
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name
                for n in ast.iter_child_nodes(node)
                if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
            ]
            classes.append((node.name, methods))
    return classes


def extract_decorators(tree: ast.Module) -> list[str]:
    """Extract decorator usage for API detection.

    Useful for identifying Flask/FastAPI routes, pytest fixtures,
    dataclasses, and other decorator-based patterns.

    Args:
        tree: Parsed AST module.

    Returns:
        List of unique decorator names used.
    """
    decorators = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Attribute):
                    decorators.append(dec.attr)
                elif isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Name):
                        decorators.append(dec.func.id)
                    elif isinstance(dec.func, ast.Attribute):
                        decorators.append(dec.func.attr)
    return list(set(decorators))


def get_module_docstring(tree: ast.Module) -> str | None:
    """Extract module-level docstring.

    Args:
        tree: Parsed AST module.

    Returns:
        The module docstring, or None if not present.
    """
    return ast.get_docstring(tree)


def get_function_docstrings(tree: ast.Module) -> dict[str, str | None]:
    """Extract docstrings for all functions.

    Args:
        tree: Parsed AST module.

    Returns:
        Dictionary mapping function names to their docstrings.
    """
    docstrings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            docstrings[node.name] = ast.get_docstring(node)
    return docstrings


def get_class_docstrings(tree: ast.Module) -> dict[str, str | None]:
    """Extract docstrings for all classes.

    Args:
        tree: Parsed AST module.

    Returns:
        Dictionary mapping class names to their docstrings.
    """
    docstrings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            docstrings[node.name] = ast.get_docstring(node)
    return docstrings


def count_lines_of_code(file_path: Path) -> int:
    """Count non-empty, non-comment lines of code.

    Args:
        file_path: Path to the Python file.

    Returns:
        Number of lines of code.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return 0

    count = 0
    in_multiline_string = False

    for line in content.splitlines():
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Handle multiline strings (docstrings)
        if '"""' in stripped or "'''" in stripped:
            quotes = '"""' if '"""' in stripped else "'''"
            occurrences = stripped.count(quotes)
            if occurrences == 1:
                in_multiline_string = not in_multiline_string
            # Count the line if it has content besides quotes
            if stripped != quotes:
                count += 1
            continue

        if in_multiline_string:
            continue

        # Skip single-line comments
        if stripped.startswith("#"):
            continue

        count += 1

    return count
