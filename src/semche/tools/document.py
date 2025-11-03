from datetime import datetime
from typing import Optional

from ..chromadb_manager import ChromaDBError, ChromaDBManager
from ..embedding import Embedder, EmbeddingError

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


def put_document(
    text: str,
    filepath: str,
    file_type: str | None = None,
    normalize: bool = False,
) -> dict:
    """テキストをベクトル化してChromaDBに保存します（upsert）。

    既存のfilepathがある場合は更新、なければ新規追加します。
    """
    try:
        # 入力バリデーション
        if not text or not text.strip():
            return {
                "status": "error",
                "message": "テキストが空です",
                "error_type": "ValidationError",
            }

        if not filepath or not filepath.strip():
            return {
                "status": "error",
                "message": "filepathが空です",
                "error_type": "ValidationError",
            }

        # ベクトル化
        embedder = _get_embedder()
        embedding = embedder.addDocument(text, normalize=normalize)

        # ChromaDBに保存
        chromadb_manager = _get_chromadb_manager()
        now = datetime.now().isoformat()
        result = chromadb_manager.save(
            embeddings=[embedding],
            documents=[text],
            filepaths=[filepath],
            updated_at=[now],
            file_types=[file_type] if file_type else None,
        )

        return {
            "status": "success",
            "message": "ドキュメントを登録しました",
            "details": {
                "count": result["count"],
                "collection": result["collection"],
                "filepath": filepath,
                "vector_dimension": len(embedding),
                "persist_directory": result["persist_directory"],
                "normalized": normalize,
            },
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
            "message": f"ChromaDB保存に失敗しました: {str(e)}",
            "error_type": "ChromaDBError",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"予期しないエラーが発生しました: {str(e)}",
            "error_type": type(e).__name__,
        }
