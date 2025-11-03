import os
import logging
from typing import List, Optional, Sequence, Dict, Any, Union
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
except ImportError as e:
    chromadb = None


class ChromaDBError(Exception):
    """ChromaDB操作に関するエラー"""
    pass


class ChromaDBManager:
    """ChromaDBへの保存（ローカル永続化）を担当するクラス。

    優先順位で永続化ディレクトリを決定:
      1) コンストラクタ引数 persist_directory
      2) 環境変数 SEMCHE_CHROMA_DIR
      3) デフォルト "./chroma_db"
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "documents",
        distance: str = "cosine",
    ) -> None:
        if chromadb is None:
            logging.error("chromadb がインストールされていません。")
            raise ChromaDBError("chromadb がインストールされていません。")

        self.persist_directory = (
            persist_directory
            or os.getenv("SEMCHE_CHROMA_DIR")
            or "./chroma_db"
        )
        self.collection_name = collection_name
        self.distance = distance

        # クライアント初期化（ローカル永続化）
        try:
            settings = Settings(anonymized_telemetry=False)
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=settings,
            )
        except Exception as e:
            logging.error(f"ChromaDBクライアント初期化に失敗: {e}")
            raise ChromaDBError(f"ChromaDBクライアント初期化に失敗: {e}")

        # コレクション取得/作成。距離関数は hnsw:space メタデータで指定
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance},
            )
        except Exception as e:
            logging.error(f"コレクション作成/取得に失敗: {e}")
            raise ChromaDBError(f"コレクション作成/取得に失敗: {e}")

    def _to_iso8601(self, value: Optional[Union[str, datetime]]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            # 厳密な検証は行わず、そのまま使用（必要に応じ強化可能）
            return value
        raise ChromaDBError("updated_at は str もしくは datetime である必要があります。")

    def _build_metadatas(
        self,
        filepaths: Sequence[str],
        updated_at: Optional[Sequence[Optional[Union[str, datetime]]]] = None,
        file_types: Optional[Sequence[Optional[str]]] = None,
    ) -> List[Dict[str, Any]]:
        n = len(filepaths)
        metas: List[Dict[str, Any]] = []
        for i in range(n):
            md: Dict[str, Any] = {"filepath": filepaths[i]}
            if updated_at is not None:
                md["updated_at"] = self._to_iso8601(updated_at[i]) if i < len(updated_at) else None
            if file_types is not None:
                md["file_type"] = file_types[i] if i < len(file_types) else None
            metas.append(md)
        return metas

    def _validate_lengths(
        self,
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str],
        filepaths: Sequence[str],
        updated_at: Optional[Sequence[Optional[Union[str, datetime]]]] = None,
        file_types: Optional[Sequence[Optional[str]]] = None,
    ) -> None:
        n = len(documents)
        if n == 0:
            raise ChromaDBError("空のデータは保存できません。")
        if len(embeddings) != n or len(filepaths) != n:
            raise ChromaDBError("embeddings/documents/filepaths の長さが一致していません。")
        if updated_at is not None and len(updated_at) not in (0, n):
            raise ChromaDBError("updated_at の長さは documents と一致する必要があります。")
        if file_types is not None and len(file_types) not in (0, n):
            raise ChromaDBError("file_types の長さは documents と一致する必要があります。")

    def save(
        self,
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str],
        filepaths: Sequence[str],
        updated_at: Optional[Sequence[Optional[Union[str, datetime]]]] = None,
        file_types: Optional[Sequence[Optional[str]]] = None,
    ) -> Dict[str, Any]:
        """ベクトルとドキュメント、メタデータを保存（id は filepaths を使用）。

        既存の id は更新（upsert）。
        """
        try:
            self._validate_lengths(embeddings, documents, filepaths, updated_at, file_types)
            metadatas = self._build_metadatas(filepaths, updated_at, file_types)

            # upsert が利用可能なら優先して使用
            if hasattr(self.collection, "upsert"):
                self.collection.upsert(
                    ids=list(filepaths),
                    embeddings=list(embeddings),
                    metadatas=metadatas,
                    documents=list(documents),
                )
            else:
                # upsert がない場合、まず追加し、失敗時は update を試す
                try:
                    self.collection.add(
                        ids=list(filepaths),
                        embeddings=list(embeddings),
                        metadatas=metadatas,
                        documents=list(documents),
                    )
                except Exception:
                    # 既存IDがあると仮定して update
                    self.collection.update(
                        ids=list(filepaths),
                        embeddings=list(embeddings),
                        metadatas=metadatas,
                        documents=list(documents),
                    )

            return {
                "status": "success",
                "collection": self.collection_name,
                "count": len(documents),
                "persist_directory": self.persist_directory,
                "distance": self.distance,
            }
        except ChromaDBError:
            raise
        except Exception as e:
            logging.error(f"ChromaDB保存に失敗: {e}")
            raise ChromaDBError(f"ChromaDB保存に失敗: {e}")

    def get_by_ids(self, ids: Sequence[str]) -> Dict[str, Any]:
        try:
            return self.collection.get(ids=list(ids))
        except Exception as e:
            logging.error(f"ChromaDB取得に失敗: {e}")
            raise ChromaDBError(f"ChromaDB取得に失敗: {e}")
