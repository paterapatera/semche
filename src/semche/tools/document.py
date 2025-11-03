import json
from datetime import datetime
from typing import Optional

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


def put_document(
    text: str,
    filepath: str,
    file_type: str | None = None,
    normalize: bool = False,
) -> str:
    """テキストをベクトル化してChromaDBに保存します（upsert）。

    既存のfilepathがある場合は更新、なければ新規追加します。
    """
    try:
        # 入力バリデーション
        if not text or not text.strip():
            return json.dumps(
                {
                    "status": "error",
                    "message": "テキストが空です",
                    "error_type": "ValidationError",
                },
                ensure_ascii=False,
                indent=2,
            )

        if not filepath or not filepath.strip():
            return json.dumps(
                {
                    "status": "error",
                    "message": "filepathが空です",
                    "error_type": "ValidationError",
                },
                ensure_ascii=False,
                indent=2,
            )

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

        return json.dumps(
            {
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
            },
            ensure_ascii=False,
            indent=2,
        )

    except EmbeddingError as e:
        return json.dumps(
            {
                "status": "error",
                "message": f"埋め込み生成に失敗しました: {str(e)}",
                "error_type": "EmbeddingError",
            },
            ensure_ascii=False,
            indent=2,
        )

    except ChromaDBError as e:
        return json.dumps(
            {
                "status": "error",
                "message": f"ChromaDB保存に失敗しました: {str(e)}",
                "error_type": "ChromaDBError",
            },
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "message": f"予期しないエラーが発生しました: {str(e)}",
                "error_type": type(e).__name__,
            },
            ensure_ascii=False,
            indent=2,
        )
