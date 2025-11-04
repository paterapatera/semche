"""BM25-based sparse encoder for hybrid search.

This module provides BM25 sparse encoding functionality for keyword-based search,
which is combined with dense vector search in hybrid retrieval.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from rank_bm25 import BM25Okapi

try:
    import MeCab
    import unidic_lite
    MECAB_AVAILABLE = True
except ImportError:
    MECAB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SparseEncoderError(Exception):
    """Sparse encoder operation errors"""

    pass


class BM25SparseEncoder:
    """BM25-based sparse encoder with persistence support.

    This encoder builds a BM25 index from documents and provides keyword-based
    search functionality. The index can be persisted to disk for reuse.

    Attributes:
        tokenizer: Function to tokenize text (default: str.split)
        bm25: BM25Okapi instance (None until index is built)
        corpus_texts: Original document texts
        corpus_ids: Document IDs corresponding to corpus_texts
    """

    def __init__(self, tokenizer: Optional[Any] = None):
        """Initialize BM25 sparse encoder.

        Args:
            tokenizer: Optional tokenizer function. If not provided, MeCab is required.
                      Should accept a string and return List[str].
        
        Raises:
            SparseEncoderError: If tokenizer is not provided and MeCab is not available.
        """
        if tokenizer:
            self.tokenizer = tokenizer
        elif MECAB_AVAILABLE:
            self.tokenizer = self._mecab_tokenizer
            # Use unidic-lite dictionary
            dic_dir = unidic_lite.DICDIR
            self._mecab_tagger = MeCab.Tagger(f"-Owakati -d {dic_dir}")
            logger.info("Using MeCab tokenizer with unidic-lite for Japanese text support")
        else:
            raise SparseEncoderError(
                "MeCab is not available. Please install mecab-python3 and unidic-lite, "
                "or provide a custom tokenizer function."
            )
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_texts: List[str] = []
        self.corpus_ids: List[str] = []

    def _mecab_tokenizer(self, text: str) -> List[str]:
        """MeCab tokenizer for Japanese text.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        return self._mecab_tagger.parse(text).strip().split()

    def _default_tokenizer(self, text: str) -> List[str]:
        """Default tokenizer: simple whitespace split and lowercase.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        return text.lower().split()

    def build_index(
        self,
        documents: Sequence[str],
        doc_ids: Sequence[str],
    ) -> Dict[str, Any]:
        """Build BM25 index from documents.

        Args:
            documents: List of document texts
            doc_ids: List of document IDs (must match length of documents)

        Returns:
            Dictionary with status and count

        Raises:
            SparseEncoderError: If input validation fails
        """
        try:
            # Validation
            if len(documents) != len(doc_ids):
                raise SparseEncoderError(
                    f"Length mismatch: {len(documents)} documents vs {len(doc_ids)} IDs"
                )

            if len(documents) == 0:
                raise SparseEncoderError("Cannot build index from empty document list")

            # Tokenize all documents
            tokenized_corpus = [self.tokenizer(doc) for doc in documents]

            # Build BM25 index
            self.bm25 = BM25Okapi(tokenized_corpus)
            self.corpus_texts = list(documents)
            self.corpus_ids = list(doc_ids)

            logger.info(f"Built BM25 index with {len(documents)} documents")

            return {
                "status": "success",
                "count": len(documents),
                "message": f"BM25 index built with {len(documents)} documents",
            }

        except SparseEncoderError:
            raise
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            raise SparseEncoderError(f"Failed to build BM25 index: {e}")

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search documents using BM25 scoring.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of dictionaries with 'id', 'text', and 'score' keys,
            sorted by score (descending)

        Raises:
            SparseEncoderError: If index is not built or search fails
        """
        try:
            if self.bm25 is None:
                raise SparseEncoderError(
                    "BM25 index not built. Call build_index() first."
                )

            # Tokenize query
            query_tokens = self.tokenizer(query)

            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)

            # Get top-k indices (sorted by score, descending)
            top_indices = scores.argsort()[-top_k:][::-1]

            # Build results
            results = []
            for idx in top_indices:
                if idx < len(self.corpus_ids):
                    results.append({
                        "id": self.corpus_ids[idx],
                        "text": self.corpus_texts[idx],
                        "score": float(scores[idx]),
                    })

            return results

        except SparseEncoderError:
            raise
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            raise SparseEncoderError(f"BM25 search failed: {e}")

    def save(self, directory: str) -> Dict[str, Any]:
        """Save BM25 index to disk.

        Args:
            directory: Directory path to save index files

        Returns:
            Dictionary with status and file paths

        Raises:
            SparseEncoderError: If index is not built or save fails
        """
        try:
            if self.bm25 is None:
                raise SparseEncoderError(
                    "No index to save. Build index first with build_index()."
                )

            # Create directory if it doesn't exist
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)

            # Save BM25 model
            bm25_path = dir_path / "bm25_index.pkl"
            with open(bm25_path, "wb") as f:
                pickle.dump(self.bm25, f)

            # Save corpus metadata (texts and IDs)
            metadata = {
                "corpus_texts": self.corpus_texts,
                "corpus_ids": self.corpus_ids,
            }
            metadata_path = dir_path / "bm25_metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved BM25 index to {directory}")

            return {
                "status": "success",
                "directory": directory,
                "files": [str(bm25_path), str(metadata_path)],
                "count": len(self.corpus_ids),
            }

        except SparseEncoderError:
            raise
        except Exception as e:
            logger.error(f"Failed to save BM25 index: {e}")
            raise SparseEncoderError(f"Failed to save BM25 index: {e}")

    def load(self, directory: str) -> Dict[str, Any]:
        """Load BM25 index from disk.

        Args:
            directory: Directory path containing index files

        Returns:
            Dictionary with status and count

        Raises:
            SparseEncoderError: If files don't exist or load fails
        """
        try:
            dir_path = Path(directory)

            # Check if files exist
            bm25_path = dir_path / "bm25_index.pkl"
            metadata_path = dir_path / "bm25_metadata.json"

            if not bm25_path.exists():
                raise SparseEncoderError(
                    f"BM25 index file not found: {bm25_path}"
                )

            if not metadata_path.exists():
                raise SparseEncoderError(
                    f"BM25 metadata file not found: {metadata_path}"
                )

            # Load BM25 model
            with open(bm25_path, "rb") as f:
                self.bm25 = pickle.load(f)

            # Load corpus metadata
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            self.corpus_texts = metadata["corpus_texts"]
            self.corpus_ids = metadata["corpus_ids"]

            logger.info(
                f"Loaded BM25 index from {directory} ({len(self.corpus_ids)} documents)"
            )

            return {
                "status": "success",
                "directory": directory,
                "count": len(self.corpus_ids),
                "message": f"Loaded {len(self.corpus_ids)} documents",
            }

        except SparseEncoderError:
            raise
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            raise SparseEncoderError(f"Failed to load BM25 index: {e}")

    def add_documents(
        self,
        documents: Sequence[str],
        doc_ids: Sequence[str],
    ) -> Dict[str, Any]:
        """Add new documents to existing index.

        This rebuilds the entire BM25 index with the new documents added.

        Args:
            documents: List of new document texts
            doc_ids: List of new document IDs

        Returns:
            Dictionary with status and total count

        Raises:
            SparseEncoderError: If validation fails
        """
        try:
            # Validation
            if len(documents) != len(doc_ids):
                raise SparseEncoderError(
                    f"Length mismatch: {len(documents)} documents vs {len(doc_ids)} IDs"
                )

            # Merge with existing corpus
            all_texts = list(self.corpus_texts) + list(documents)
            all_ids = list(self.corpus_ids) + list(doc_ids)

            # Rebuild index
            return self.build_index(all_texts, all_ids)

        except SparseEncoderError:
            raise
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise SparseEncoderError(f"Failed to add documents: {e}")
