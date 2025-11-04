"""Hybrid retriever combining dense (Chroma) and sparse (BM25) search.

This module provides a simple interface to perform hybrid search by combining
LangChain's Chroma vectorstore (dense) and a BM25-based sparse encoder using
Reciprocal Rank Fusion (RRF). We explicitly implement RRF to avoid depending
on EnsembleRetriever availability across LangChain versions.

Default weights are 0.5 for dense and 0.5 for sparse as agreed.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .chromadb_manager import ChromaDBError, ChromaDBManager
from .sparse_encoder import BM25SparseEncoder

logger = logging.getLogger(__name__)


class HybridRetrieverError(Exception):
    pass


class HybridRetriever:
    """Hybrid search using EnsembleRetriever (dense + sparse).

    - Dense: Chroma vectorstore retriever (provided by ChromaDBManager.vectorstore)
    - Sparse: BM25 retriever built from all documents in ChromaDB
    - Fusion: RRF via EnsembleRetriever with weights [0.5, 0.5]
    """

    def __init__(
        self,
        chroma_manager: ChromaDBManager,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
    ) -> None:
        self.chroma = chroma_manager
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

        if self.chroma.vectorstore is None:
            raise HybridRetrieverError(
                "Chroma vectorstore is not initialized. Provide embedding_function when creating ChromaDBManager."
            )

    def _sparse_scores(
        self, query: str, where: Optional[Dict[str, Any]] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Compute BM25 scores and return top results as list of {id, score, metadata, document}.
        
        Only returns items with score > eps (1e-12) to avoid zero-score items affecting RRF ranking.
        """
        items = self.chroma.get_all_documents(where=where, include_documents=True)
        if not items:
            return []
        texts = [it.get("document") or "" for it in items]
        ids = [it.get("metadata", {}).get("filepath") or it.get("id") for it in items]

        encoder = BM25SparseEncoder()
        encoder.build_index(texts, ids)
        sparse_top = encoder.search(query, top_k=max(1, int(top_k)))

        # Map scores back to full item info
        id_to_item = {}
        for it in items:
            key = (it.get("metadata", {}).get("filepath") or it.get("id"))
            id_to_item[key] = it

        eps = 1e-12
        results: List[Dict[str, Any]] = []
        for r in sparse_top:
            score = float(r["score"])
            # Filter out zero or near-zero scores to prevent unrelated items from affecting RRF
            if score <= eps:
                continue
            it = id_to_item.get(r["id"]) or {}
            results.append({
                "id": r["id"],
                "score": score,
                "metadata": it.get("metadata", {}),
                "document": it.get("document"),
            })
        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        rrf_constant: int = 60,
    ) -> List[Dict[str, Any]]:
        """Execute hybrid search and return ranked item dicts.

        Each item: {id, document, metadata, score}
        """
        try:
            k = max(1, int(top_k))
            # Dense: similarity_search_with_relevance_scores (text)
            dense_pairs = self.chroma.vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=k * 2,
                filter=where if where else None,
            )
            dense_rank: Dict[str, int] = {}
            id_to_item: Dict[str, Dict[str, Any]] = {}
            for idx, (doc, _score) in enumerate(dense_pairs, start=1):
                md = doc.metadata or {}
                did = md.get("filepath") or md.get("id") or str(idx)
                dense_rank[did] = idx
                id_to_item[did] = {
                    "id": did,
                    "document": doc.page_content,
                    "metadata": md,
                }

            # Sparse
            sparse_list = self._sparse_scores(query=query, where=where, top_k=k * 2)
            sparse_rank: Dict[str, int] = {}
            for idx, item in enumerate(sparse_list, start=1):
                sparse_rank[item["id"]] = idx
                # Prefer dense doc text if exists, else use sparse's
                if item["id"] not in id_to_item:
                    id_to_item[item["id"]] = {
                        "id": item["id"],
                        "document": item.get("document"),
                        "metadata": item.get("metadata", {}),
                    }

            # RRF fusion
            def rrf(rank: Optional[int]) -> float:
                return 0.0 if rank is None else 1.0 / (rrf_constant + rank)

            all_ids = set(dense_rank) | set(sparse_rank)
            scored: List[Dict[str, Any]] = []
            for did in all_ids:
                score = (
                    self.dense_weight * rrf(dense_rank.get(did))
                    + self.sparse_weight * rrf(sparse_rank.get(did))
                )
                item = id_to_item.get(did, {"id": did, "document": None, "metadata": {}})
                scored.append({
                    **item,
                    "score": float(score),
                })

            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:k]
        except ChromaDBError:
            raise
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise HybridRetrieverError(f"Hybrid search failed: {e}")
