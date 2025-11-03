# delete.py 詳細設計書

## 概要

`delete_document` は、ChromaDBに保存されたドキュメントを filepath（ID）を指定して削除するMCPツールです。存在しないIDが指定された場合はエラーにせず、`deleted_count=0` として成功レスポンスを返します。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/tools/delete.py`
- 呼び出し元: `/home/pater/semche/src/semche/mcp_server.py`
- テスト: `/home/pater/semche/tests/test_delete.py`

## 利用クラス・ライブラリ（ファイルパス一覧）

- `ChromaDBManager`（ChromaDB 永続化管理）
  - 実装: `/home/pater/semche/src/semche/chromadb_manager.py`
  - 使用メソッド: `delete(ids: Sequence[str]) -> dict`
- `ChromaDBError`（ChromaDB 操作時の例外）
  - 実装: `/home/pater/semche/src/semche/chromadb_manager.py`
- 標準ライブラリ
  - なし（実装内では外部リソースを直接扱わない）

## 関数仕様

### `delete_document(filepath: str) -> dict`

- 役割: 指定IDのドキュメントを削除し、結果を辞書で返却
- 引数:
  - `filepath` (str): 削除対象のID（パス文字列）
- 返り値: `dict`
  - 成功（削除あり）: `{status: "success", message: "ドキュメントを削除しました", deleted_count: 1, filepath, collection, persist_directory}`
  - 成功（該当なし）: `{status: "success", message: "削除対象が見つかりませんでした", deleted_count: 0, filepath, collection, persist_directory}`
  - 失敗: `{status: "error", message, error_type}`
- 例外: 関数外へは投げず、辞書へ変換して返却

## 内部処理フロー

```
delete_document(filepath)
  ├─ 入力バリデーション（filepath の空チェック）
  ├─ chroma = _get_chromadb_manager()  # 遅延初期化
  ├─ res = chroma.delete([filepath])
  ├─ deleted_count = res["deleted_count"]
  ├─ deleted_count == 0 ?
  │     └─ success(該当なし) を返却
  └─ success(削除あり) を返却
```

## エラー仕様

| ケース                   | 返却形式/内容                                      |
| ------------------------ | -------------------------------------------------- |
| `filepath` が空/空白のみ | `{status: "error", error_type: "ValidationError"}` |
| ChromaDB削除に失敗       | `{status: "error", error_type: "ChromaDBError"}`   |
| 想定外の例外             | `{status: "error", error_type: <例外クラス名>}`    |

## 設計ポリシー

- 例外は外部へは投げず、MCPの応答として構造化辞書で返却
- `ChromaDBManager` はモジュール内シングルトン（遅延初期化）を使用して初期化コストを抑制
- 非存在IDはエラーにせず、成功（該当なし）で返却（クライアントの利便性のため）

## 変更履歴

### v0.2.1 (2025-11-03)

- **追加**: `delete_document()` ツールを新規実装
  - 非存在ID時は `deleted_count=0` で成功扱い
  - 例外は辞書化して返却
