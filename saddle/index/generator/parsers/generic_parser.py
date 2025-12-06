#!/usr/bin/env python3
"""Generic parser for languages not covered by specialized parsers.

Uses tree-sitter with automatic language detection based on file extension.
Provides basic structure extraction that works across many languages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GenericParseResult:
    """Result of parsing with generic parser."""

    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    language: str = ""


# Extension to tree-sitter language mapping
EXTENSION_TO_LANGUAGE = {
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".lua": "lua",
    ".r": "r",
    ".R": "r",
    ".jl": "julia",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".ml": "ocaml",
    ".vim": "vim",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "fish",
}

# Language-specific query patterns for function extraction
FUNCTION_QUERIES = {
    "go": "(function_declaration name: (identifier) @func)",
    "rust": "(function_item name: (identifier) @func)",
    "ruby": "(method name: (identifier) @func)",
    "java": "(method_declaration name: (identifier) @func)",
    "c": "(function_definition declarator: (function_declarator declarator: (identifier) @func))",
    "cpp": "(function_definition declarator: (function_declarator declarator: (identifier) @func))",
    "c_sharp": "(method_declaration name: (identifier) @func)",
    "php": "(function_definition name: (name) @func)",
    "swift": "(function_declaration name: (simple_identifier) @func)",
    "kotlin": "(function_declaration (simple_identifier) @func)",
    "scala": "(function_definition name: (identifier) @func)",
    "lua": "(function_declaration name: (identifier) @func)",
    "bash": "(function_definition name: (word) @func)",
}

# Language-specific query patterns for class extraction
CLASS_QUERIES = {
    "go": "(type_declaration (type_spec name: (type_identifier) @class))",
    "rust": "(struct_item name: (type_identifier) @class)",
    "ruby": "(class name: (constant) @class)",
    "java": "(class_declaration name: (identifier) @class)",
    "cpp": "(class_specifier name: (type_identifier) @class)",
    "c_sharp": "(class_declaration name: (identifier) @class)",
    "php": "(class_declaration name: (name) @class)",
    "swift": "(class_declaration name: (type_identifier) @class)",
    "kotlin": "(class_declaration (type_identifier) @class)",
    "scala": "(class_definition name: (identifier) @class)",
}


def get_language_for_extension(ext: str) -> str | None:
    """Map file extension to tree-sitter language name.

    Args:
        ext: File extension including the dot (e.g., '.go').

    Returns:
        Tree-sitter language name, or None if not supported.
    """
    return EXTENSION_TO_LANGUAGE.get(ext.lower())


def parse_file(file_path: Path) -> GenericParseResult | None:
    """Parse file using tree-sitter with auto-detected language.

    Args:
        file_path: Path to the source file to parse.

    Returns:
        GenericParseResult with extracted information, or None if parsing fails.
    """
    lang = get_language_for_extension(file_path.suffix)
    if not lang:
        return None

    try:
        from tree_sitter_languages import get_language, get_parser
    except ImportError:
        # tree-sitter not available
        return GenericParseResult(language=lang)

    try:
        parser = get_parser(lang)
        language = get_language(lang)
    except Exception:
        # Language not supported by tree-sitter-languages
        return GenericParseResult(language=lang)

    try:
        content = file_path.read_bytes()
        tree = parser.parse(content)
    except (FileNotFoundError, PermissionError):
        return None

    functions = _extract_functions(tree.root_node, language, content, lang)
    classes = _extract_classes(tree.root_node, language, content, lang)

    return GenericParseResult(
        functions=functions,
        classes=classes,
        language=lang,
    )


def _node_text(node, content: bytes) -> str:
    """Extract text content from a tree-sitter node."""
    return content[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _extract_functions(root_node, language, content: bytes, lang: str) -> list[str]:
    """Extract function definitions using language-specific queries."""
    functions = []

    query_text = FUNCTION_QUERIES.get(lang)
    if not query_text:
        return functions

    try:
        query = language.query(query_text)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "func":
                functions.append(_node_text(node, content))
    except Exception:
        pass

    return list(set(functions))


def _extract_classes(root_node, language, content: bytes, lang: str) -> list[str]:
    """Extract class/struct/type definitions using language-specific queries."""
    classes = []

    query_text = CLASS_QUERIES.get(lang)
    if not query_text:
        return classes

    try:
        query = language.query(query_text)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "class":
                classes.append(_node_text(node, content))
    except Exception:
        pass

    return list(set(classes))


def is_supported(file_path: Path) -> bool:
    """Check if a file's language is supported by this parser.

    Args:
        file_path: Path to check.

    Returns:
        True if the file extension is supported.
    """
    return file_path.suffix.lower() in EXTENSION_TO_LANGUAGE


def get_supported_extensions() -> list[str]:
    """Get list of supported file extensions.

    Returns:
        List of supported extensions including the dot.
    """
    return list(EXTENSION_TO_LANGUAGE.keys())


def count_lines_of_code(file_path: Path) -> int:
    """Count non-empty, non-comment lines of code.

    This is a simple heuristic that works across languages.

    Args:
        file_path: Path to the source file.

    Returns:
        Number of lines of code.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return 0

    count = 0
    in_multiline_comment = False
    comment_start = "/*"
    comment_end = "*/"

    for line in content.splitlines():
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Handle multiline comments (C-style)
        if comment_start in stripped and comment_end in stripped:
            # Single-line block comment - check if there's code too
            before_comment = stripped.split(comment_start)[0].strip()
            after_comment = stripped.split(comment_end)[-1].strip()
            if before_comment or after_comment:
                count += 1
            continue

        if comment_start in stripped:
            before = stripped.split(comment_start)[0].strip()
            if before:
                count += 1
            in_multiline_comment = True
            continue

        if comment_end in stripped:
            in_multiline_comment = False
            after = stripped.split(comment_end)[-1].strip()
            if after:
                count += 1
            continue

        if in_multiline_comment:
            continue

        # Skip common single-line comment patterns
        if (
            stripped.startswith("//")
            or stripped.startswith("#")
            or stripped.startswith("--")
            or stripped.startswith(";")
        ):
            continue

        count += 1

    return count
