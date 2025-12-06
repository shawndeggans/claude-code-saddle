"""Codebase auto-indexing system for Claude Code Saddle.

This package provides tools for generating structural indexes
of codebases, including function/class extraction, dependency
graphs, and staleness detection.
"""

from .index_generator import run_indexer

__all__ = ["run_indexer"]
