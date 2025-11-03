# document.py 詳細設計書

## 概要

`put_document` はテキストをベクトル化して ChromaDB に保存（upsert）するツール関数です。ファイルパスを ID として用い、同一の `filepath` を指定した場合は上書き保存（更新）を行います。MCP サーバー（`mcp_server.py`）からツールとして公開され、実際の処理は本モジュールに実装されています。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/tools/document.py`
- 呼び出し元: `/home/pater/semche/src/semche/mcp_server.py`
- 設計: `/home/pater/semche/src/semche/mcp_server.py.exp.md`（委譲説明あり）
- テスト: `/home/pater/semche/tests/test_mcp_server.py`

## 利用クラス・ライブラリ（ファイルパス一覧）

- `Embedder`（ベクトル埋め込み）
  - 実装ファイル: `/home/pater/semche/src/semche/embedding.py`
- `EmbeddingError`（埋め込み時の例外）
  - 実装ファイル: `/home/pater/semche/src/semche/embedding.py`
- `ChromaDBManager`（ChromaDB 永続化管理）
  - 実装ファイル: `/home/pater/semche/src/semche/chromadb_manager.py`
- `ChromaDBError`（ChromaDB 操作時の例外）
  - 実装ファイル: `/home/pater/semche/src/semche/chromadb_manager.py`
- 標準ライブラリ
  - `json`（レスポンス生成）
  - `datetime.datetime`（ISO8601 タイムスタンプ生成）

## 設計ポリシー

- モジュール内シングルトン（遅延初期化）
  - `Embedder` と `ChromaDBManager` は初回呼び出し時に生成し、以降は再利用
  - モデルロード・クライアント接続を最小化し、パフォーマンスを確保
- ID 設計
  - `filepath` を ID として利用し upsert を実現
- メタデータ
  - `filepath`, `updated_at`（ISO8601）, `file_type` を保存

## 関数仕様

### `put_document(text: str, filepath: str, file_type: str | None = None, normalize: bool = False) -> str`

- 役割: テキストを埋め込み → ChromaDB に保存（upsert）し、JSON 文字列で結果を返す
- 引数:
  - `text`: 登録するテキスト（必須, 非空チェックあり）
  - `filepath`: ドキュメントの ID として扱うパス（必須, 非空チェックあり）
  - `file_type`: 任意のファイルタイプ（例: `"spec"`, `"jira"`）
  - `normalize`: 埋め込みベクトルの L2 正規化を行うか（デフォルト `False`）
- 返り値: `str` JSON 文字列
  - 成功時: `{"status": "success", "details": { ... }}`
  - 失敗時: `{"status": "error", "error_type": "..."}`
- 例外: 関数外へは投げず、JSON へ変換して返却

## 内部処理フロー

```
put_document(text, filepath, file_type, normalize)
  ├─ 入力バリデーション（text, filepath の空チェック）
  ├─ embedder = _get_embedder()  # 遅延初期化
  ├─ embedding = embedder.addDocument(text, normalize)
  ├─ chroma = _get_chromadb_manager()  # 遅延初期化
  ├─ now = datetime.now().isoformat()
  ├─ result = chroma.save(
  │     embeddings=[embedding],
  │     documents=[text],
  │     filepaths=[filepath],
  │     updated_at=[now],
  │     file_types=[file_type] or None,
  │  )
  └─ JSON を生成して返却
```

## エラー仕様

| ケース                   | 例外型          | 返却形式/内容                                      |
| ------------------------ | --------------- | -------------------------------------------------- |
| `text` が空/空白のみ     | ValidationError | `{status: "error", error_type: "ValidationError"}` |
| `filepath` が空/空白のみ | ValidationError | 同上                                               |
| 埋め込み生成に失敗       | EmbeddingError  | `{status: "error", error_type: "EmbeddingError"}`  |
| ChromaDB 保存に失敗      | ChromaDBError   | `{status: "error", error_type: "ChromaDBError"}`   |
| 想定外の例外             | Exception       | `{status: "error", error_type: <例外クラス名>}`    |

## パフォーマンス考慮

- `Embedder` のモデルロードは初回のみ（キャッシュ）
- `ChromaDBManager` は同一プロセス内で再利用
- 正規化はオプション（必要に応じて有効化）

## セキュリティ・入力妥当性

- `filepath` は任意文字列として受け取る（実ファイルアクセスは行わない）
- 機密情報のメタデータ保存を避けることを推奨
- 大きすぎるテキストの取り扱いは将来の要件に応じて制限可能

## テスト

- `tests/test_mcp_server.py` にて以下を検証
  - 正常: 単一登録、正規化、`file_type` なし、同一 `filepath` で更新
  - 異常: 空テキスト、空白のみ、空 `filepath`
  - 連続登録（複数件連続で成功する）

## 参考/関連

- `src/semche/embedding.py`（Embedder 実装）
- `src/semche/chromadb_manager.py`（ChromaDBManager 実装）
- `src/semche/mcp_server.py`（FastMCP 登録側）
