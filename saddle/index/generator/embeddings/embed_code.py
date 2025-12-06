#!/usr/bin/env python3
"""Code embedding generation for semantic search capabilities.

This module provides optional semantic search functionality using
vector embeddings. It chunks code by function/class and stores
embeddings in ChromaDB for efficient querying.

Dependencies (optional):
    - chromadb: Vector database
    - sentence-transformers: Embedding generation
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    pass


def is_available() -> bool:
    """Check if embedding dependencies are available.

    Returns:
        True if chromadb and sentence-transformers are installed.
    """
    try:
        import chromadb  # noqa: F401
        import sentence_transformers  # noqa: F401

        return True
    except ImportError:
        return False


def chunk_code_by_function(
    file_path: Path, file_index: dict[str, Any]
) -> Generator[dict[str, Any], None, None]:
    """Split code into function-level chunks for embedding.

    Args:
        file_path: Path to the source file.
        file_index: Index entry for the file with functions/classes.

    Yields:
        Dictionaries with 'id', 'text', and 'metadata' keys.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return

    lines = content.splitlines()

    # If we have no structural info, yield the whole file
    if not file_index.get("functions") and not file_index.get("classes"):
        chunk_id = hashlib.md5(str(file_path).encode()).hexdigest()[:12]
        yield {
            "id": f"{chunk_id}_file",
            "text": content[:10000],  # Limit chunk size
            "metadata": {
                "file_path": str(file_path),
                "chunk_type": "file",
                "start_line": 1,
                "end_line": len(lines),
            },
        }
        return

    # Yield chunks for each function (simplified - in reality would need AST)
    for func_name in file_index.get("functions", []):
        # Find function in content (simplified heuristic)
        for i, line in enumerate(lines):
            if f"def {func_name}" in line or f"function {func_name}" in line:
                # Extract function body (simplified - takes next 50 lines max)
                start_line = i
                end_line = min(i + 50, len(lines))
                func_text = "\n".join(lines[start_line:end_line])

                chunk_id = hashlib.md5(
                    f"{file_path}:{func_name}".encode()
                ).hexdigest()[:12]

                yield {
                    "id": chunk_id,
                    "text": func_text,
                    "metadata": {
                        "file_path": str(file_path),
                        "chunk_type": "function",
                        "function_name": func_name,
                        "start_line": start_line + 1,
                        "end_line": end_line,
                    },
                }
                break


def generate_embedding(
    text: str, model_name: str = "all-MiniLM-L6-v2"
) -> list[float] | None:
    """Generate embedding vector for text using sentence-transformers.

    Args:
        text: The text to embed.
        model_name: Name of the sentence-transformers model to use.

    Returns:
        List of floats representing the embedding, or None if unavailable.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None

    try:
        model = SentenceTransformer(model_name)
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception:
        return None


def init_vector_store(persist_directory: Path):
    """Initialize ChromaDB vector store.

    Args:
        persist_directory: Directory to store the database.

    Returns:
        ChromaDB collection, or None if unavailable.
    """
    try:
        import chromadb
    except ImportError:
        return None

    try:
        client = chromadb.PersistentClient(path=str(persist_directory))
        collection = client.get_or_create_collection(
            name="codebase", metadata={"hnsw:space": "cosine"}
        )
        return collection
    except Exception:
        return None


def index_codebase(
    codebase_index: dict[str, Any],
    project_path: Path,
    persist_directory: Path,
) -> int:
    """Index entire codebase into vector store.

    Args:
        codebase_index: The codebase-index.json content.
        project_path: Root path of the project.
        persist_directory: Directory for ChromaDB storage.

    Returns:
        Number of chunks indexed, or 0 if embeddings unavailable.
    """
    if not is_available():
        return 0

    collection = init_vector_store(persist_directory)
    if collection is None:
        return 0

    chunk_count = 0
    ids = []
    documents = []
    metadatas = []

    for file_path_str, file_info in codebase_index.items():
        file_path = Path(file_path_str)
        if not file_path.exists():
            file_path = project_path / file_path_str
        if not file_path.exists():
            continue

        for chunk in chunk_code_by_function(file_path, file_info):
            ids.append(chunk["id"])
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])
            chunk_count += 1

            # Batch upsert every 100 chunks
            if len(ids) >= 100:
                try:
                    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                except Exception:
                    pass
                ids = []
                documents = []
                metadatas = []

    # Final batch
    if ids:
        try:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        except Exception:
            pass

    return chunk_count


def query_codebase(
    query: str,
    persist_directory: Path,
    n_results: int = 5,
) -> list[dict[str, Any]]:
    """Query codebase using semantic search.

    Args:
        query: Natural language query (e.g., "Where is authentication handled?").
        persist_directory: Directory containing ChromaDB storage.
        n_results: Maximum number of results to return.

    Returns:
        List of result dictionaries with 'file_path', 'chunk_type', etc.
    """
    if not is_available():
        return []

    collection = init_vector_store(persist_directory)
    if collection is None:
        return []

    try:
        results = collection.query(query_texts=[query], n_results=n_results)
    except Exception:
        return []

    output = []
    if results and results.get("metadatas"):
        for i, metadata in enumerate(results["metadatas"][0]):
            result = {
                "file_path": metadata.get("file_path", ""),
                "chunk_type": metadata.get("chunk_type", ""),
                "function_name": metadata.get("function_name", ""),
                "start_line": metadata.get("start_line", 0),
                "end_line": metadata.get("end_line", 0),
            }
            if results.get("documents"):
                result["snippet"] = results["documents"][0][i][:200]
            if results.get("distances"):
                result["distance"] = results["distances"][0][i]
            output.append(result)

    return output
