from typing import Optional, Dict, Any, List

from ..embedding import Embedder, EmbeddingError
from ..chromadb_manager import ChromaDBManager, ChromaDBError

# Module-level singletons (lazy init)
_embedder: Optional[Embedder] = None
_chromadb_manager: Optional[ChromaDBManager] = None


def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def _get_chromadb_manager() -> ChromaDBManager:
    global _chromadb_manager
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBManager()
    return _chromadb_manager


def search(
    query: str,
    top_k: int = 5,
    file_type: Optional[str] = None,
    filepath_prefix: Optional[str] = None,
    normalize: bool = False,
    min_score: Optional[float] = None,
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
        if min_score is not None and not (0.0 <= min_score <= 1.0):
            return {
                "status": "error",
                "message": "min_score は 0.0〜1.0 の範囲で指定してください",
                "error_type": "ValidationError",
            }

        # クエリ埋め込み
        embedder = _get_embedder()
        qvec = embedder.addDocument(query, normalize=normalize)

        # メタデータフィルタ
        where = {}
        if file_type:
            where["file_type"] = file_type

        chroma = _get_chromadb_manager()
        raw = chroma.query(query_embeddings=[qvec], top_k=top_k, where=where, include_documents=include_documents)

        # 追加フィルタ（prefix, min_score）
        results = raw.get("results", [])
        filtered: List[Dict[str, Any]] = []
        for item in results:
            if filepath_prefix and item.get("filepath") and not str(item["filepath"]).startswith(filepath_prefix):
                continue
            score = item.get("score")
            if min_score is not None and (score is None or score < min_score):
                continue
            # documentのプレビュー制限（過剰な内容を避ける）
            doc = item.get("document") if include_documents else None
            if isinstance(doc, str) and len(doc) > 500:
                doc = doc[:500] + "..."
            filtered.append({
                "filepath": item.get("filepath"),
                "score": score,
                "document": doc,
                "metadata": item.get("metadata", {}),
            })

        # スコアで降順ソート
        filtered.sort(key=lambda x: (x["score"] is not None, x["score"]), reverse=True)

        return {
            "status": "success",
            "message": "検索が完了しました",
            "results": filtered,
            "count": len(filtered),
            "query_vector_dimension": len(qvec) if isinstance(qvec, list) else None,
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
