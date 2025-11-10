# get_by_prefix.py 詳細設計書

## 概要

`get_documents_by_prefix` は、id（filepath）の前方一致＋file_type完全一致でドキュメントを取得するMCPツールです。ChromaDBのSQLiteファイルを直接操作して検索を行います。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/tools/get_by_prefix.py`
- テスト: `/home/pater/semche/tests/test_get_by_prefix.py`（未作成）

## 利用クラス・ライブラリ

- `ChromaDBManager`（内部モジュール: chromadb_manager.py）
  - 用途: ChromaDB操作のマネージャー
- 標準ライブラリ
  - `typing` (Any, Dict, List, Optional)

## 関数設計

### get_documents_by_prefix()

- 目的: id（filepath）の前方一致＋file_type完全一致でドキュメントを取得
- 入力:
  - `prefix: str` id（filepath）の前方一致条件（必須）
  - `file_type: str` 完全一致条件（必須）
  - `include_documents: bool` 本文を含めるか（デフォルト True）
  - `top_k: int | None` 最大取得件数（省略時は全件）
- 実装:
  - 入力バリデーション（空チェック、top_k > 0）
  - `ChromaDBManager.get_documents_by_prefix()` を呼び出し
  - 結果をMCPレスポンス形式に整形
- 戻り値: `{status, prefix, file_type, include_documents, top_k, count, results}` または `{status: "error", message, error_type}`
- エラー処理: ChromaDBError, ValidationError, UnexpectedError

## 入出力例

```python
from src.semche.tools.get_by_prefix import get_documents_by_prefix

result = get_documents_by_prefix(
    prefix="/src/",
    file_type="code",
    include_documents=True,
    top_k=5
)
# {"status": "success", "count": 2, "results": [{"id": "/src/main.py", "document": "...", "file_type": "code"}, ...]}
```

## エラー仕様

| ケース           | 例外/返却       | ログ |
| ---------------- | --------------- | ---- |
| prefix空         | ValidationError | -    |
| file_type空      | ValidationError | -    |
| top_k <= 0       | ValidationError | -    |
| ChromaDB操作失敗 | ChromaDBError   | -    |
| 予期せぬエラー   | UnexpectedError | -    |

## パフォーマンス/設計上の注意

- ChromaDBManagerのシングルトンインスタンスを共有
- SQLite直クエリのため、ChromaDBバージョン変更時は要検証
- 大量データ時はtop_kで件数制限を推奨

## 変更履歴

### v0.1.0 (初回リリース)

- **実装**: get_documents_by_prefix MCPツール
- **実装**: ChromaDBManagerとの連携
- **実装**: 入力バリデーションとエラー処理
