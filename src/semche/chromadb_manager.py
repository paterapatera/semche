import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Union

try:
    import chromadb
    from chromadb.config import Settings
    from langchain_chroma import Chroma
except ImportError:
    chromadb = None
    Chroma = None  # type: ignore[misc]


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
        embedding_function: Optional[Any] = None,
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
        self.embedding_function = embedding_function

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

        # LangChain Chroma vectorstore（オプショナル）
        self.vectorstore: Optional[Any] = None
        if embedding_function and Chroma is not None:
            try:
                self.vectorstore = Chroma(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding_function=embedding_function,
                )
            except Exception as e:
                logging.warning(f"LangChain Chroma初期化に失敗（フォールバック可能）: {e}")
                self.vectorstore = None

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
    ) -> List[Dict[str, Union[str, None]]]:
        n = len(filepaths)
        metas: List[Dict[str, Union[str, None]]] = []
        for i in range(n):
            md: Dict[str, Union[str, None]] = {"filepath": filepaths[i]}
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
                    metadatas=metadatas,  # type: ignore[arg-type] # ChromaDBの型定義が厳格すぎるため
                    documents=list(documents),
                )
            else:
                # upsert がない場合、まず追加し、失敗時は update を試す
                try:
                    self.collection.add(
                        ids=list(filepaths),
                        embeddings=list(embeddings),
                        metadatas=metadatas,  # type: ignore[arg-type] # ChromaDBの型定義が厳格すぎるため
                        documents=list(documents),
                    )
                except Exception:
                    # 既存IDがあると仮定して update
                    self.collection.update(
                        ids=list(filepaths),
                        embeddings=list(embeddings),
                        metadatas=metadatas,  # type: ignore[arg-type] # ChromaDBの型定義が厳格すぎるため
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
            result = self.collection.get(ids=list(ids))
            return dict(result)
        except Exception as e:
            logging.error(f"ChromaDB取得に失敗: {e}")
            raise ChromaDBError(f"ChromaDB取得に失敗: {e}")

    def delete(self, ids: Sequence[str]) -> Dict[str, Any]:
        """指定したIDのドキュメントを削除する。

        戻り値には削除件数（推定）を含む。Chromaのdeleteは件数を返さないため、
        事前にget()で存在確認して件数をカウントする。
        """
        try:
            ids_list = list(ids)
            # 事前に存在件数を確認
            before = self.get_by_ids(ids_list)
            existing_ids = set(before.get("ids", []))
            to_delete = [i for i in ids_list if i in existing_ids]

            # 削除実行（存在しないIDが混じっていても問題なし）
            self.collection.delete(ids=ids_list)

            return {
                "status": "success",
                "collection": self.collection_name,
                "persist_directory": self.persist_directory,
                "deleted_count": len(to_delete),
                "ids": ids_list,
            }
        except ChromaDBError:
            raise
        except Exception as e:
            logging.error(f"ChromaDB削除に失敗: {e}")
            raise ChromaDBError(f"ChromaDB削除に失敗: {e}")

    def get_all_documents(
        self,
        where: Optional[Dict[str, Any]] = None,
        include_documents: bool = True,
    ) -> List[Dict[str, Any]]:
        """コレクション内の全ドキュメントを取得する。

        注意: ドキュメント数が多い場合はメモリ使用量が増えるため、将来的にページング対応を検討。

        Args:
            where: メタデータフィルタ
            include_documents: 本文を含めるか

        Returns:
            List[Dict]: {id, document, metadata}
        """
        try:
            include_fields: List[str] = ["metadatas"]
            if include_documents:
                include_fields.append("documents")

            # Chromaのgetは引数なしで全件取得できる実装が多いが、環境差異に備えtry/except
            res = self.collection.get(
                where=where if where else None,
                include=include_fields,  # type: ignore[arg-type]
            )

            ids = res.get("ids", []) or []
            metadatas = res.get("metadatas", []) or []
            documents = res.get("documents", []) or []

            items: List[Dict[str, Any]] = []
            for i, _id in enumerate(ids):
                md = metadatas[i] if i < len(metadatas) else {}
                doc = documents[i] if include_documents and i < len(documents) else None
                items.append({
                    "id": _id,
                    "document": doc,
                    "metadata": md,
                })
            return items
        except Exception as e:
            logging.error(f"ChromaDB全件取得に失敗: {e}")
            raise ChromaDBError(f"ChromaDB全件取得に失敗: {e}")

    def query(
        self,
        query_embeddings: Sequence[Sequence[float]],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include_documents: bool = True,
    ) -> Dict[str, Any]:
        """クエリベクトルで近傍検索を行う。

        Returns ChromaDBのquery結果をラップした辞書。
        1件のクエリを想定（query_embeddings[0]）。
        
        LangChain Chromaを使用して検索を実行。
        """
        try:
            if self.vectorstore is None:
                raise ChromaDBError(
                    "LangChain Chromaが初期化されていません。"
                    "embedding_functionを指定してChromaDBManagerを初期化してください。"
                )
            
            query_vec = list(query_embeddings[0])
            
            # similarity_search_by_vector_with_relevance_scores を使用
            results = self.vectorstore.similarity_search_by_vector_with_relevance_scores(
                embedding=query_vec,
                k=int(max(1, top_k)),
                filter=where if where else None,
            )
            
            # 結果を既存の形式に変換
            items: List[Dict[str, Any]] = []
            for doc, score in results:
                # LangChainはsimilarityスコアを返す（0〜1、高いほど類似）
                metadata = doc.metadata or {}
                items.append({
                    "id": metadata.get("filepath"),  # filepathをIDとして使用
                    "filepath": metadata.get("filepath"),
                    "score": score,
                    "document": doc.page_content if include_documents else None,
                    "metadata": {
                        "file_type": metadata.get("file_type"),
                        "updated_at": metadata.get("updated_at"),
                    },
                })
            
            return {
                "status": "success",
                "collection": self.collection_name,
                "persist_directory": self.persist_directory,
                "distance": self.distance,
                "results": items,
                "count": len(items),
            }
        except ChromaDBError:
            raise
        except Exception as e:
            logging.error(f"ChromaDB検索に失敗: {e}")
            raise ChromaDBError(f"ChromaDB検索に失敗: {e}")
