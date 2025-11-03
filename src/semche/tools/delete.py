from typing import Optional

from ..chromadb_manager import ChromaDBError, ChromaDBManager
from ..embedding import Embedder

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
        embedder = _get_embedder()
        # EmbedderのHuggingFaceEmbeddingsインスタンスをembedding_functionとして渡す
        _chromadb_manager = ChromaDBManager(embedding_function=embedder.embeddings)
    return _chromadb_manager


def delete_document(filepath: str) -> dict:
    """指定したfilepath(ID)のドキュメントを削除します。

    成功時は削除件数（0または1）を返します。存在しない場合もエラーにはせず、
    deleted_count=0を返却します。
    """
    try:
        # 入力バリデーション
        if not filepath or not filepath.strip():
            return {
                "status": "error",
                "message": "filepathが空です",
                "error_type": "ValidationError",
            }

        chroma = _get_chromadb_manager()
        res = chroma.delete([filepath])
        deleted_count = int(res.get("deleted_count", 0))

        if deleted_count == 0:
            return {
                "status": "success",
                "message": "削除対象が見つかりませんでした",
                "deleted_count": 0,
                "filepath": filepath,
                "collection": res.get("collection"),
                "persist_directory": res.get("persist_directory"),
            }
        else:
            return {
                "status": "success",
                "message": "ドキュメントを削除しました",
                "deleted_count": deleted_count,
                "filepath": filepath,
                "collection": res.get("collection"),
                "persist_directory": res.get("persist_directory"),
            }

    except ChromaDBError as e:
        return {
            "status": "error",
            "message": f"ChromaDB削除に失敗しました: {str(e)}",
            "error_type": "ChromaDBError",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"予期しないエラーが発生しました: {str(e)}",
            "error_type": type(e).__name__,
        }
