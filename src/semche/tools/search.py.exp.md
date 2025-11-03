# search.py 詳細設計書

## 概要

`search` はクエリ文字列をベクトル化し、ChromaDB に保存済みのドキュメントからセマンティック類似検索を行うツール関数です。MCP サーバー（`mcp_server.py`）から `@mcp.tool()` で公開されます。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/tools/search.py`
- 呼び出し元: `/home/pater/semche/src/semche/mcp_server.py`
- 設計: `/home/pater/semche/src/semche/tools/search.py.exp.md`
- 依存: `/home/pater/semche/src/semche/embedding.py`, `/home/pater/semche/src/semche/chromadb_manager.py`
- テスト: `/home/pater/semche/tests/test_search.py`

## 利用クラス・ライブラリ（ファイルパス一覧）

- `Embedder` / `EmbeddingError`: `/home/pater/semche/src/semche/embedding.py`
- `ChromaDBManager` / `ChromaDBError`: `/home/pater/semche/src/semche/chromadb_manager.py`
- 標準ライブラリ: `datetime`（現状は未使用、拡張用）

## 関数仕様

### `search(query: str, top_k: int = 5, file_type: Optional[str] = None, filepath_prefix: Optional[str] = None, normalize: bool = False, min_score: Optional[float] = None, include_documents: bool = True) -> dict`

- 役割: クエリ埋め込み → ChromaDB 近傍検索 → 結果を dict で返却
- 引数:
  - `query`: 検索クエリ文字列（必須, 非空）
  - `top_k`: 上位件数（>=1）
  - `file_type`: メタデータ `file_type` でフィルタ
  - `filepath_prefix`: 取得後に `filepath` の接頭辞でフィルタ
  - `normalize`: クエリベクトルのL2正規化
  - `min_score`: 類似度の下限（0.0〜1.0）
  - `include_documents`: ドキュメント本文プレビューを含めるか
- 返り値: `dict`
  - 成功時: `{status, message, results: [{filepath, score, document?, metadata}], count, query_vector_dimension, persist_directory}`
  - 失敗時: `{status: "error", message, error_type}`

## 内部処理フロー

```
search(...)
  ├─ バリデーション（query, top_k, min_score）
  ├─ qvec = Embedder.addDocument(query, normalize)
  ├─ where = {file_type?}
  ├─ raw = ChromaDBManager.query([qvec], top_k, where, include_documents)
  ├─ results = raw["results"] を prefix/min_score でフィルタ
  ├─ document を最大500文字に制限（include_documents=True時）
  ├─ score 降順ソート
  └─ dict で返却
```

## エラー仕様

- `ValidationError`: 空クエリ、top_k<=0、min_scoreが範囲外
- `EmbeddingError`: 埋め込み生成失敗
- `ChromaDBError`: クエリ実行失敗
- その他例外: `error_type` にクラス名を入れて返却

## パフォーマンス/制限

- `top_k` は適切な上限を設けることを推奨（例: 50）
- document プレビューは最大500文字に制限
- 将来的に `where_document` や前処理キャッシュの導入余地あり

## 備考

- Chroma の距離（cosine）は `1.0 - distance` で類似度に変換
- `filepath_prefix` は Chroma の where では表現しづらいため取得後フィルタで対応
