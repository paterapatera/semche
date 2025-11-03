# chromadb_manager.py 詳細設計書

## 概要

`ChromaDBManager`は、ローカル永続化モードのChromaDBに対してベクトルデータ・原文ドキュメント・メタデータを保存（upsert）するためのユーティリティクラスです。コレクションはデフォルト`documents`、距離関数は`cosine`（変更可能）を採用します。IDにはファイルパスを使用し、同一ファイルは更新扱いとなります。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/chromadb_manager.py`
- テスト: `/home/pater/semche/tests/test_chromadb_manager.py`

## 利用クラス・ライブラリ

- `chromadb.PersistentClient`（外部ライブラリ: chromadb）
  - ファイルパス: 外部パッケージ
  - 用途: ローカル永続化クライアント
- `chromadb.config.Settings`
  - 用途: テレメトリ設定（anonymized_telemetry=False）
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
    def __init__(self, persist_directory: str | None = None, collection_name: str = "documents", distance: str = "cosine")
    def save(self, embeddings, documents, filepaths, updated_at=None, file_types=None) -> dict
    def get_by_ids(self, ids) -> dict
```

#### 初期化

- 永続化ディレクトリの解決順序
  1. コンストラクタ引数 `persist_directory`
  2. 環境変数 `SEMCHE_CHROMA_DIR`
  3. 既定値 `./chroma_db`
- クライアント作成: `chromadb.PersistentClient(path, settings=Settings(anonymized_telemetry=False))`
- コレクション取得/作成: `get_or_create_collection(name, metadata={"hnsw:space": distance})`

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

#### get_by_ids()

- 目的: 保存済みデータの取得（テストや検証用途）
- 実装: `collection.get(ids=[...])`

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

## 変更履歴

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
