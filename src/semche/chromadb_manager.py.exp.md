# chromadb_manager.py 詳細設計書

## 概要

`ChromaDBManager`は、ローカル永続化モードのChromaDBに対してベクトルデータ・原文ドキュメント・メタデータを保存（upsert）および検索するためのユーティリティクラスです。

- LangChainの`Chroma`ベクトルストアとの統合
- `query()`メソッドで`similarity_search_by_vector_with_score()`を使用（LangChain経由）
- 既存のネイティブAPIへのフォールバック機能を維持
- 将来のハイブリッド検索（dense + sparse）への拡張を見据えた設計

コレクションはデフォルト`documents`、距離関数は`cosine`（変更可能）を採用します。IDにはファイルパスを使用し、同一ファイルは更新扱いとなります。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/chromadb_manager.py`
- テスト: `/home/pater/semche/tests/test_chromadb_manager.py`

## 利用クラス・ライブラリ

- `chromadb.PersistentClient`（外部ライブラリ: chromadb）
  - ファイルパス: 外部パッケージ
  - 用途: ローカル永続化クライアント
- `chromadb.config.Settings`
  - 用途: テレメトリ設定（anonymized_telemetry=False）
- `langchain_chroma.Chroma`（外部ライブラリ: langchain-chroma）
  - ファイルパス: 外部パッケージ
  - 用途: LangChainベクトルストア統合
- 標準ライブラリ
  - `os`, `logging`, `datetime`, `typing` (Any, Dict, List, Literal, Optional, Sequence, Union)

## 型アノテーション・型チェック対応

### type ignoreコメントの使用

本モジュールでは、ChromaDBライブラリの型定義との互換性のため、以下の箇所で`# type: ignore`を使用しています：

```python
metadatas=metadatas,  # type: ignore[arg-type] # ChromaDBの型定義が厳格すぎるため
```

**理由**: ChromaDBの`Collection.upsert()`, `Collection.add()`, `Collection.update()`のメタデータ型定義が厳格で、実用的な`Dict[str, Union[str, None]]`型を受け付けないため、型チェックを抑制しています。実行時には問題なく動作します。

### 型定義の改善

- `_build_metadatas()`の戻り値型を`List[Dict[str, Union[str, None]]]`に明示
- `query()`の`include`パラメータにLiteral型を使用して、ChromaDBが受け付ける値を厳密に定義：
  ```python
  include_fields: List[Literal["documents", "embeddings", "metadatas", "distances", "uris", "data"]]
  ```
- Literal型のインポートを追加（Python 3.8+）

## クラス設計

### 例外クラス

- `ChromaDBError`: ChromaDB操作に関する例外を一元化

### ChromaDBManager

```python
class ChromaDBManager:
    def __init__(self, persist_directory: str | None = None, collection_name: str = "documents", distance: str = "cosine", embedding_function: Any | None = None)
    def save(self, embeddings, documents, filepaths, updated_at=None, file_types=None) -> dict
    def get_by_ids(self, ids) -> dict
    def delete(self, ids) -> dict
    def query(self, query_embeddings, top_k=5, where=None, include_documents=True) -> dict
```

#### 初期化

- 永続化ディレクトリの解決順序
  1. コンストラクタ引数 `persist_directory`
  2. 環境変数 `SEMCHE_CHROMA_DIR`
  3. 既定値 `./chroma_db`
- クライアント作成: `chromadb.PersistentClient(path, settings=Settings(anonymized_telemetry=False))`
- コレクション取得/作成: `get_or_create_collection(name, metadata={"hnsw:space": distance})`
  - `embedding_function`が渡された場合、`Chroma`ベクトルストアを初期化
  - `self.vectorstore`: LangChainの`Chroma`インスタンス（オプショナル）
  - 初期化失敗時は警告を出してフォールバック（`vectorstore = None`）

#### save()

- 目的: upsertでの保存（同一IDは更新）
- 入力:
  - `embeddings: list[list[float]]` ベクトル
  - `documents: list[str]` 元文
  - `filepaths: list[str]` IDとして使用
  - `updated_at: list[str|datetime]|None` ISO8601を期待（datetimeはisoformat変換）
  - `file_types: list[str]|None` 任意の文字列
- 検証:
  - 空でないこと
  - 各リスト長が一致
- メタデータ生成:
  - 各要素 `{"filepath", "updated_at", "file_type"}`
- upsert実装:
  - `collection.upsert(...)` があれば使用
  - なければ `collection.add(...)` で追加、失敗時 `collection.update(...)` で更新
- 戻り値例:
  - `{status: "success", collection: "documents", count: n, persist_directory: ..., distance: ...}`
- **注**: LangChain統合後もネイティブAPIを継続使用（upsertロジックの複雑さを維持）

#### query()

- **[v0.3.0] LangChain統合による変更**
- 目的: ベクトルクエリで近傍検索
- 入力:
  - `query_embeddings: list[list[float]]` クエリベクトル（最初の要素を使用）
  - `top_k: int` 上位k件（デフォルト5）
  - `where: dict|None` メタデータフィルタ
  - `include_documents: bool` ドキュメント本文を含めるか
- **実装方式**:
  - **必須**: `embedding_function`が初期化時に渡されている必要がある
  - `self.vectorstore`が`None`の場合はエラー
  - LangChainの`similarity_search_by_vector_with_relevance_scores()`を使用
  - 引数:
    - `embedding`: クエリベクトル（単一）
    - `k`: 取得件数
    - `filter`: メタデータフィルタ（`where`パラメータをそのまま渡す）
  - 返却:
    - `[(Document, relevance_score), ...]`形式
    - `Document.page_content`: ドキュメント本文
    - `Document.metadata`: メタデータ辞書
    - `relevance_score`: 類似度スコア（0〜1、高いほど類似）
- 戻り値形式（既存と互換）:
  ```python
  {
    "status": "success",
    "collection": "documents",
    "persist_directory": "./chroma_db",
    "distance": "cosine",
    "results": [
      {
        "id": "filepath",
        "filepath": "filepath",
        "score": 0.85,  # 類似度（0〜1、高いほど類似）
        "document": "本文" | None,
        "metadata": {"file_type": ..., "updated_at": ...}
      }
    ],
    "count": 件数
  }
  ```

#### get_by_ids()

- 目的: 保存済みデータの取得（テストや検証用途）
- 実装: `collection.get(ids=[...])`

#### delete()

- 目的: 指定したID群のドキュメントを削除
- 実装方針:
  - Chromaの`delete()`は削除件数を返さないため、事前に`get_by_ids()`で存在IDを特定し、推定削除件数（`deleted_count`）を算出
  - その後に`collection.delete(ids=...)`を実行
- 返却値例:
  - `{status: "success", collection: "documents", persist_directory: "./chroma_db", deleted_count: n, ids: [...]}`
- エラー時は `ChromaDBError` を送出

## 入出力例

```python
from src.semche.chromadb_manager import ChromaDBManager

mgr = ChromaDBManager(persist_directory="./chroma_db", collection_name="documents")
res = mgr.save(
    embeddings=[[0.1, 0.2, 0.3]],
    documents=["仕様書v1"],
    filepaths=["/docs/spec.md"],
    updated_at=["2025-11-03T12:00:00"],
    file_types=["spec"],
)
print(res)
# {"status": "success", "collection": "documents", "count": 1, ...}
```

## エラー仕様

| ケース                       | 例外          | ログ  |
| ---------------------------- | ------------- | ----- |
| chromadb未インストール       | ChromaDBError | error |
| クライアント初期化失敗       | ChromaDBError | error |
| コレクション作成/取得失敗    | ChromaDBError | error |
| 入力検証エラー               | ChromaDBError | error |
| 保存・取得中の予期せぬエラー | ChromaDBError | error |

## パフォーマンス/設計上の注意

- upsertを優先使用し、ない場合はadd→updateで代替
- メタデータは必要なキーのみ設定
- 距離関数は`cosine`（用途により`l2`/`ip`へ変更可）
- モデルの次元数はChroma側で固定検証しないため、呼び出し側で一貫性を担保する
- `embedding_function`が渡されない場合は従来のネイティブAPIで動作（後方互換性）

## 変更履歴

### v0.3.0 (2025-11-03)

- **追加**: LangChain統合による検索機能の改善
  - `__init__()`に`embedding_function`パラメータを追加（オプショナル）
  - `self.vectorstore`: LangChain Chromaインスタンス（`embedding_function`が渡された場合）
  - `query()`メソッドでLangChainの`similarity_search_by_vector_with_score()`を使用
  - `_query_via_langchain()`: LangChain経由の検索実装
  - `_query_native()`: 既存ネイティブAPIのフォールバック実装
- **改善**: 将来のハイブリッド検索（dense + sparse）への拡張を見据えた設計
- **互換性**: 既存のAPIインターフェースを完全維持
- **依存関係**: `langchain-chroma>=1.0.0`を追加

### v0.2.1 (2025-11-03)

- **追加**: `delete()` メソッドを追加
  - 事前存在確認に基づく`deleted_count`の算出
  - `collection.delete(ids=...)` による削除実行

### v0.2.0 (2025-11-03)

- **改善**: 型アノテーションの精度向上
  - `_build_metadatas()`の戻り値型を`List[Dict[str, Union[str, None]]]`に明示
  - `query()`の`include`パラメータにLiteral型を使用
- **改善**: type ignoreコメントの標準化
  - エラーコード`[arg-type]`を明示
  - ChromaDBの型定義との互換性問題を説明
- **追加**: Literal型のインポート

### v0.1.0 (初回リリース)

- **実装**: ChromaDBManagerクラスの基本機能
- **実装**: upsert対応の保存機能
- **実装**: メタデータ管理（filepath, updated_at, file_type）
- **実装**: 永続化ディレクトリの柔軟な設定

## 参考

- ChromaDB Docs: https://docs.trychroma.com/
- Python Client: https://docs.trychroma.com/reference/py-client
- LangChain Chroma: https://python.langchain.com/docs/integrations/vectorstores/chroma
