"""CLI tool for bulk document registration to ChromaDB.

This module provides a command-line interface to register multiple documents
from files, directories, and wildcard patterns into ChromaDB with vector embeddings.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from semche.chromadb_manager import ChromaDBError, ChromaDBManager
from semche.embedding import Embedder, ensure_single_vector

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Bulk register documents to ChromaDB with vector embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register all markdown files in docs directory
  doc-update ./docs/**/*.md --file-type note

  # Register with ID prefix
  doc-update ./project --id-prefix myproject --file-type code

  # Filter by date and ignore patterns
  doc-update ./wiki --filter-from-date 2025-11-01 --ignore "**/.git/**"

  # Specify ChromaDB directory
  doc-update ./notes --chroma-dir /tmp/chroma --file-type memo
        """,
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="File paths, directories, or wildcard patterns (e.g., **/*.md)",
    )
    parser.add_argument(
        "--id-prefix",
        default="",
        help="Prefix for document IDs (e.g., 'abc' → 'abc:path/to/file.md')",
    )
    parser.add_argument(
        "--file-type",
        default="none",
        help="File type for metadata (default: none)",
    )
    parser.add_argument(
        "--filter-from-date",
        help="Only register files modified after this date (YYYY-MM-DD or ISO8601)",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Glob pattern to ignore (can be specified multiple times)",
    )
    parser.add_argument(
        "--chroma-dir",
        help="ChromaDB persist directory (overrides SEMCHE_CHROMA_DIR)",
    )
    return parser.parse_args()


def parse_date_filter(date_str: str) -> datetime:
    """Parse date filter string to datetime.
    
    Supports:
    - YYYY-MM-DD
    - YYYY-MM-DDTHH:MM:SS
    - Full ISO8601
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try ISO8601 with timezone
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or ISO8601")


def should_ignore(path: Path, ignore_patterns: List[str]) -> bool:
    """Check if path matches any ignore pattern."""
    for pattern in ignore_patterns:
        if path.match(pattern):
            return True
    return False


def is_binary_file(file_path: Path) -> bool:
    """Check if file is binary by reading first 8KB."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            if b"\0" in chunk:
                return True
        return False
    except Exception:
        return True


def resolve_inputs(
    inputs: List[str],
    ignore_patterns: List[str],
    filter_date: Optional[datetime],
    cwd: Path,
) -> List[Path]:
    """Resolve input patterns to list of file paths.
    
    Args:
        inputs: List of file paths, directories, or wildcard patterns
        ignore_patterns: List of glob patterns to ignore
        filter_date: Only include files modified after this date
        cwd: Current working directory for relative path resolution
    
    Returns:
        List of resolved file paths
    """
    resolved: set[Path] = set()
    
    for input_str in inputs:
        input_path = Path(input_str)
        
        # Handle wildcard patterns
        if "**" in input_str or "*" in input_str:
            # Use cwd as base for glob
            if input_path.is_absolute():
                base = Path("/")
                pattern = str(input_path.relative_to("/"))
            else:
                base = cwd
                pattern = input_str
            
            for match in base.glob(pattern):
                if match.is_file():
                    resolved.add(match.resolve())
        
        # Handle directory
        elif input_path.is_dir():
            for file_path in input_path.rglob("*"):
                if file_path.is_file():
                    resolved.add(file_path.resolve())
        
        # Handle single file
        elif input_path.is_file():
            resolved.add(input_path.resolve())
        else:
            logger.warning(f"Input not found: {input_str}")
    
    # Apply filters
    filtered: List[Path] = []
    for path in sorted(resolved):
        # Check ignore patterns
        if should_ignore(path, ignore_patterns):
            logger.debug(f"Ignored (pattern match): {path}")
            continue
        
        # Check date filter
        if filter_date:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime < filter_date:
                logger.debug(f"Ignored (too old): {path}")
                continue
        
        filtered.append(path)
    
    return filtered


def generate_document_id(file_path: Path, cwd: Path, prefix: str) -> str:
    """Generate document ID from file path.
    
    Args:
        file_path: Absolute path to file
        cwd: Current working directory
        prefix: Optional prefix for ID
    
    Returns:
        Document ID (e.g., "prefix:relative/path/to/file.md")
    """
    try:
        rel_path = file_path.relative_to(cwd)
    except ValueError:
        # If file is outside cwd, use absolute path
        rel_path = file_path
    
    # Convert to forward slashes for consistency
    id_path = str(rel_path).replace(os.sep, "/")
    
    if prefix:
        return f"{prefix}:{id_path}"
    return id_path


def read_file_content(file_path: Path) -> Optional[str]:
    """Read file content as UTF-8 text.
    
    Returns None if file is binary or cannot be read.
    """
    # Check if binary
    if is_binary_file(file_path):
        logger.debug(f"Skipped (binary): {file_path}")
        return None
    
    # Try to read as UTF-8
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Skip empty or whitespace-only content
        if not content or not content.strip():
            logger.debug(f"Skipped (empty): {file_path}")
            return None
        
        return content
    except UnicodeDecodeError:
        logger.warning(f"Skipped (encoding error): {file_path}")
        return None
    except Exception as e:
        logger.warning(f"Skipped (read error): {file_path}: {e}")
        return None


def process_files(
    file_paths: List[Path],
    cwd: Path,
    id_prefix: str,
    file_type: str,
    embedder: Embedder,
) -> Tuple[List[List[float]], List[str], List[str], List[str], List[str]]:
    """Process files to prepare for bulk registration.
    
    Returns:
        Tuple of (embeddings, documents, ids, updated_at_list, file_types)
    """
    embeddings: List[List[float]] = []
    documents: List[str] = []
    ids: List[str] = []
    updated_at_list: List[str] = []
    file_types: List[str] = []
    
    skipped = 0
    
    for file_path in file_paths:
        # Read content
        content = read_file_content(file_path)
        if content is None:
            skipped += 1
            continue
        
        # Generate ID
        doc_id = generate_document_id(file_path, cwd, id_prefix)
        
        # Get file modification time
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        updated_at = mtime.isoformat()
        
        # Generate embedding
        try:
            embedding = embedder.addDocument(content)
            vector = ensure_single_vector(embedding)
        except Exception as e:
            logger.warning(f"Failed to embed: {file_path}: {e}")
            skipped += 1
            continue
        
        # Add to batch
        embeddings.append(vector)
        documents.append(content)
        ids.append(doc_id)
        updated_at_list.append(updated_at)
        file_types.append(file_type)
        
        logger.info(f"Processed: {doc_id}")
    
    if skipped > 0:
        logger.info(f"Skipped {skipped} files (binary/empty/error)")
    
    return embeddings, documents, ids, updated_at_list, file_types


def main() -> int:
    """Main entry point for CLI."""
    args = parse_args()
    
    # Get current working directory
    cwd = Path.cwd()
    
    # Parse date filter if provided
    filter_date: Optional[datetime] = None
    if args.filter_from_date:
        try:
            filter_date = parse_date_filter(args.filter_from_date)
            logger.info(f"Filtering files modified after: {filter_date}")
        except ValueError as e:
            logger.error(str(e))
            return 1
    
    # Resolve input files
    logger.info("Resolving input files...")
    try:
        file_paths = resolve_inputs(
            args.inputs,
            args.ignore,
            filter_date,
            cwd,
        )
    except Exception as e:
        logger.error(f"Failed to resolve inputs: {e}")
        return 1
    
    if not file_paths:
        logger.error("No files found matching the input patterns")
        return 1
    
    logger.info(f"Found {len(file_paths)} files to process")
    
    # Initialize embedder and ChromaDB manager
    try:
        embedder = Embedder()
        chroma_mgr = ChromaDBManager(persist_directory=args.chroma_dir)
        logger.info(f"ChromaDB directory: {chroma_mgr.persist_directory}")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return 1
    
    # Process files
    logger.info("Processing files...")
    try:
        embeddings, documents, ids, updated_at_list, file_types = process_files(
            file_paths,
            cwd,
            args.id_prefix,
            args.file_type,
            embedder,
        )
    except Exception as e:
        logger.error(f"Failed to process files: {e}")
        return 1
    
    if not ids:
        logger.error("No documents to register (all files skipped)")
        return 1
    
    # Save to ChromaDB
    logger.info(f"Registering {len(ids)} documents to ChromaDB...")
    try:
        result = chroma_mgr.save(
            embeddings=embeddings,
            documents=documents,
            filepaths=ids,
            updated_at=updated_at_list,
            file_types=file_types,
        )
        logger.info(f"✓ Successfully registered {result['count']} documents")
        logger.info(f"  Collection: {result['collection']}")
        logger.info(f"  Directory: {result['persist_directory']}")
        return 0
    except ChromaDBError as e:
        logger.error(f"Failed to save to ChromaDB: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
