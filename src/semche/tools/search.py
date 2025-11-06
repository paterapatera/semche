from typing import Any, Dict, List, Optional

from ..chromadb_manager import ChromaDBError, ChromaDBManager
from ..hybrid_retriever import HybridRetriever, HybridRetrieverError
from .document import _get_chromadb_manager  # reuse the same singleton

# Module-level singletons (lazy init)
_chromadb_manager: Optional[ChromaDBManager] = None


# _get_chromadb_manager is imported from document.py to share the same instance


def search(
    query: str,
    top_k: int = 5,
    file_type: Optional[str] = None,
    include_documents: bool = True,
    max_content_length: Optional[int] = None,
) -> Dict[str, Any]:
    """クエリでハイブリッド検索（dense + sparse, RRF）を行う。

    Args:
        query: 検索クエリ文字列
        top_k: 取得する上位件数（デフォルト: 5）
        file_type: メタデータのfile_typeでフィルタ（オプション）
        include_documents: ドキュメント本文を含めるか（デフォルト: True）
        max_content_length: ドキュメント内容の最大文字数。Noneの場合は全文取得（デフォルト: None）

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

        # メタデータフィルタ
        where = {}
        if file_type:
            where["file_type"] = file_type

        chroma = _get_chromadb_manager()

        # ハイブリッド検索実行
        retriever = HybridRetriever(chroma_manager=chroma, dense_weight=0.5, sparse_weight=0.5)
        items = retriever.search(query=query, top_k=top_k, where=where or None)

    # 結果の整形
        formatted: List[Dict[str, Any]] = []
        for rank, item in enumerate(items):
            score = float(item.get("score", 0.0))
            # documentの文字数制限（オプション）
            content = item.get("document") if include_documents else None
            if isinstance(content, str) and max_content_length is not None and len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            md = item.get("metadata", {}) or {}
            formatted.append({
                "filepath": md.get("filepath"),
                "score": score,
                "document": content,
                "metadata": md,
            })

        return {
            "status": "success",
            "message": "ハイブリッド検索が完了しました",
            "results": formatted,
            "count": len(formatted),
            "query_vector_dimension": None,
            "persist_directory": chroma.persist_directory,
        }

    except HybridRetrieverError as e:
        return {
            "status": "error",
            "message": f"ハイブリッド検索に失敗しました: {str(e)}",
            "error_type": type(e).__name__,
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
