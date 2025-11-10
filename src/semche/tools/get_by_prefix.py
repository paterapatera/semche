from typing import Any, Dict, List, Optional

from ..chromadb_manager import ChromaDBError, ChromaDBManager
from .document import _get_chromadb_manager  # reuse the same singleton

# Module-level singletons (lazy init)
_chromadb_manager: Optional[ChromaDBManager] = None


# _get_chromadb_manager is imported from document.py to share the same instance


def get_documents_by_prefix(
    prefix: str,
    file_type: str,
    include_documents: bool = True,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """id（filepath）の前方一致＋file_type完全一致でドキュメントを取得します。

    ChromaDBのSQLiteを直接操作して検索を行います。

    Args:
        prefix: id（filepath）の前方一致条件（必須）
        file_type: 完全一致条件（必須）
        include_documents: 本文を含めるか（デフォルト: True）
        top_k: 最大取得件数（省略時は全件）

    Returns:
        Dict: 検索結果を含む辞書
    """
    try:
        # 入力バリデーション
        if not prefix or not prefix.strip():
            return {
                "status": "error",
                "message": "prefixが空です",
                "error_type": "ValidationError",
            }

        if not file_type or not file_type.strip():
            return {
                "status": "error",
                "message": "file_typeが空です",
                "error_type": "ValidationError",
            }

        if top_k is not None and top_k <= 0:
            return {
                "status": "error",
                "message": "top_k は 1 以上である必要があります",
                "error_type": "ValidationError",
            }

        # ChromaDBManagerインスタンス取得
        mgr = _get_chromadb_manager()

        # 検索実行
        results = mgr.get_documents_by_prefix(
            prefix=prefix,
            file_type=file_type,
            include_documents=include_documents,
            top_k=top_k,
        )

        return {
            "status": "success",
            "prefix": prefix,
            "file_type": file_type,
            "include_documents": include_documents,
            "top_k": top_k,
            "count": len(results),
            "results": results,
        }

    except ChromaDBError as e:
        return {
            "status": "error",
            "message": f"ChromaDB操作エラー: {str(e)}",
            "error_type": "ChromaDBError",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"予期せぬエラー: {str(e)}",
            "error_type": "UnexpectedError",
        }
