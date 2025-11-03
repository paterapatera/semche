from typing import Any, Dict, List, Optional

from ..chromadb_manager import ChromaDBError, ChromaDBManager
from ..embedding import Embedder, EmbeddingError, ensure_single_vector
from .document import _get_chromadb_manager  # reuse the same singleton

# Module-level singletons (lazy init)
_embedder: Optional[Embedder] = None
_chromadb_manager: Optional[ChromaDBManager] = None


def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


# _get_chromadb_manager is imported from document.py to share the same instance


def search(
    query: str,
    top_k: int = 5,
    file_type: Optional[str] = None,
    include_documents: bool = True,
) -> Dict[str, Any]:
    """クエリでセマンティック検索を行う（ChromaDB）。

    Returns a structured dict suitable for MCP Inspector rendering.
    """
    try:
        if not query or not query.strip():
            return {
                "status": "error",
                "message": "クエリが空です",
                "error_type": "ValidationError",
            }
        if top_k <= 0:
            return {
                "status": "error",
                "message": "top_k は 1 以上である必要があります",
                "error_type": "ValidationError",
            }

        # クエリ埋め込み
        embedder = _get_embedder()
        qvec = embedder.addDocument(query)
        query_vec = ensure_single_vector(qvec)

        # メタデータフィルタ
        where = {}
        if file_type:
            where["file_type"] = file_type

        chroma = _get_chromadb_manager()
        raw = chroma.query(
            query_embeddings=[query_vec],
            top_k=top_k,
            where=where,
            include_documents=include_documents
        )

        # 結果の整形
        results = raw.get("results", [])
        formatted: List[Dict[str, Any]] = []
        for item in results:
            # documentのプレビュー制限（過剰な内容を避ける）
            doc = item.get("document") if include_documents else None
            if isinstance(doc, str) and len(doc) > 500:
                doc = doc[:500] + "..."
            formatted.append({
                "filepath": item.get("filepath"),
                "score": item.get("score"),
                "document": doc,
                "metadata": item.get("metadata", {}),
            })

        return {
            "status": "success",
            "message": "検索が完了しました",
            "results": formatted,
            "count": len(formatted),
            "query_vector_dimension": len(query_vec) if isinstance(query_vec, list) else None,
            "persist_directory": raw.get("persist_directory"),
        }

    except EmbeddingError as e:
        return {
            "status": "error",
            "message": f"埋め込み生成に失敗しました: {str(e)}",
            "error_type": "EmbeddingError",
        }
    except ChromaDBError as e:
        return {
            "status": "error",
            "message": f"ChromaDB検索に失敗しました: {str(e)}",
            "error_type": "ChromaDBError",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"予期しないエラーが発生しました: {str(e)}",
            "error_type": type(e).__name__,
        }
