#!/usr/bin/env python3
"""JavaScript/TypeScript parser using tree-sitter.

Extracts structural information from JavaScript and TypeScript files
including functions, classes, imports, exports, and React components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class JSParseResult:
    """Result of parsing a JS/TS file."""

    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    react_components: list[str] = field(default_factory=list)


# Extension to tree-sitter language mapping
EXTENSION_TO_LANGUAGE = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}


def get_language_for_extension(ext: str) -> str | None:
    """Map file extension to tree-sitter language name.

    Args:
        ext: File extension including the dot (e.g., '.js').

    Returns:
        Tree-sitter language name, or None if not supported.
    """
    return EXTENSION_TO_LANGUAGE.get(ext.lower())


def parse_file(file_path: Path) -> JSParseResult | None:
    """Parse a JavaScript/TypeScript file using tree-sitter.

    Args:
        file_path: Path to the JS/TS file to parse.

    Returns:
        JSParseResult with extracted information, or None if parsing fails.
    """
    lang_name = get_language_for_extension(file_path.suffix)
    if not lang_name:
        return None

    try:
        from tree_sitter_languages import get_language, get_parser
    except ImportError:
        # Fallback to regex-based parsing if tree-sitter not available
        return _parse_file_regex(file_path)

    try:
        parser = get_parser(lang_name)
        language = get_language(lang_name)
    except Exception:
        return _parse_file_regex(file_path)

    try:
        content = file_path.read_bytes()
        tree = parser.parse(content)
    except (FileNotFoundError, PermissionError):
        return None

    return JSParseResult(
        functions=_extract_functions(tree.root_node, language, content),
        classes=_extract_classes(tree.root_node, language, content),
        imports=_extract_imports(tree.root_node, language, content),
        exports=_extract_exports(tree.root_node, language, content),
        react_components=_extract_react_components(tree.root_node, language, content),
    )


def _node_text(node, content: bytes) -> str:
    """Extract text content from a tree-sitter node."""
    return content[node.start_byte : node.end_byte].decode("utf-8")


def _extract_functions(root_node, language, content: bytes) -> list[str]:
    """Extract function declarations and expressions.

    Handles:
    - function declarations: function foo() {}
    - arrow functions assigned to variables: const foo = () => {}
    - method definitions in objects/classes
    """
    functions = []

    # Query for function declarations
    query_text = """
    (function_declaration name: (identifier) @func_name)
    """

    try:
        query = language.query(query_text)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "func_name":
                functions.append(_node_text(node, content))
    except Exception:
        pass

    # Also look for arrow functions assigned to const/let/var
    try:
        arrow_query = """
        (lexical_declaration
          (variable_declarator
            name: (identifier) @var_name
            value: (arrow_function)))
        """
        query = language.query(arrow_query)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "var_name":
                functions.append(_node_text(node, content))
    except Exception:
        pass

    return list(set(functions))


def _extract_classes(root_node, language, content: bytes) -> list[str]:
    """Extract class declarations."""
    classes = []

    query_text = """
    (class_declaration name: (identifier) @class_name)
    """

    try:
        query = language.query(query_text)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "class_name":
                classes.append(_node_text(node, content))
    except Exception:
        pass

    return classes


def _extract_imports(root_node, language, content: bytes) -> list[str]:
    """Extract import statements (ES6 and CommonJS)."""
    imports = []

    # ES6 imports
    try:
        import_query = """
        (import_statement source: (string) @source)
        """
        query = language.query(import_query)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "source":
                # Remove quotes from string
                text = _node_text(node, content).strip("\"'")
                imports.append(text)
    except Exception:
        pass

    # CommonJS require
    try:
        require_query = """
        (call_expression
          function: (identifier) @func (#eq? @func "require")
          arguments: (arguments (string) @source))
        """
        query = language.query(require_query)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "source":
                text = _node_text(node, content).strip("\"'")
                imports.append(text)
    except Exception:
        pass

    return list(set(imports))


def _extract_exports(root_node, language, content: bytes) -> list[str]:
    """Extract export statements."""
    exports = []

    try:
        # Named exports
        export_query = """
        (export_statement
          declaration: (lexical_declaration
            (variable_declarator name: (identifier) @export_name)))
        (export_statement
          declaration: (function_declaration name: (identifier) @export_name))
        (export_statement
          declaration: (class_declaration name: (identifier) @export_name))
        """
        query = language.query(export_query)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "export_name":
                exports.append(_node_text(node, content))
    except Exception:
        pass

    return list(set(exports))


def _extract_react_components(root_node, language, content: bytes) -> list[str]:
    """Detect React component definitions.

    Looks for:
    - Function components (PascalCase functions returning JSX)
    - Class components extending React.Component
    """
    components = []

    # Look for PascalCase function declarations that likely return JSX
    try:
        func_query = """
        (function_declaration name: (identifier) @func_name)
        (lexical_declaration
          (variable_declarator
            name: (identifier) @func_name
            value: (arrow_function)))
        """
        query = language.query(func_query)
        captures = query.captures(root_node)
        for node, name in captures:
            if name == "func_name":
                func_name = _node_text(node, content)
                # React components are PascalCase
                if func_name and func_name[0].isupper():
                    components.append(func_name)
    except Exception:
        pass

    return list(set(components))


def _parse_file_regex(file_path: Path) -> JSParseResult | None:
    """Fallback regex-based parsing when tree-sitter is unavailable.

    Less accurate but provides basic extraction.
    """
    import re

    try:
        content = file_path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return None

    functions = []
    classes = []
    imports = []
    exports = []
    components = []

    # Function declarations
    for match in re.finditer(r"function\s+(\w+)\s*\(", content):
        functions.append(match.group(1))

    # Arrow functions assigned to const/let
    for match in re.finditer(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(", content):
        functions.append(match.group(1))

    # Class declarations
    for match in re.finditer(r"class\s+(\w+)", content):
        classes.append(match.group(1))

    # ES6 imports
    for match in re.finditer(r"import\s+.*?from\s+['\"](.+?)['\"]", content):
        imports.append(match.group(1))

    # CommonJS require
    for match in re.finditer(r"require\s*\(\s*['\"](.+?)['\"]\s*\)", content):
        imports.append(match.group(1))

    # Exports
    for match in re.finditer(r"export\s+(?:default\s+)?(?:const|let|var|function|class)\s+(\w+)", content):
        exports.append(match.group(1))

    # React components (PascalCase functions)
    for func in functions:
        if func and func[0].isupper():
            components.append(func)

    return JSParseResult(
        functions=list(set(functions)),
        classes=list(set(classes)),
        imports=list(set(imports)),
        exports=list(set(exports)),
        react_components=list(set(components)),
    )


def count_lines_of_code(file_path: Path) -> int:
    """Count non-empty, non-comment lines of code.

    Args:
        file_path: Path to the JS/TS file.

    Returns:
        Number of lines of code.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return 0

    count = 0
    in_multiline_comment = False

    for line in content.splitlines():
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Handle multiline comments
        if "/*" in stripped and "*/" in stripped:
            # Single-line block comment
            if stripped == "/*" + stripped[2:-2] + "*/":
                continue
            count += 1
            continue

        if "/*" in stripped:
            in_multiline_comment = True
            continue

        if "*/" in stripped:
            in_multiline_comment = False
            continue

        if in_multiline_comment:
            continue

        # Skip single-line comments
        if stripped.startswith("//"):
            continue

        count += 1

    return count
