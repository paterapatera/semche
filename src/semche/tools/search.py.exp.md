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
- `ensure_single_vector`: `/home/pater/semche/src/semche/embedding.py`
  - 用途: クエリの埋め込み結果を単一ベクトル形式（`List[float]`）に統一
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
  ├─ query_vec = ensure_single_vector(qvec)  # 単一ベクトルに正規化
  ├─ where = {file_type?}
  ├─ raw = ChromaDBManager.query([query_vec], top_k, where, include_documents)
  ├─ results = raw["results"] を prefix/min_score でフィルタ
  ├─ document を最大500文字に制限（include_documents=True時）
  ├─ score 降順ソート
  └─ dict で返却
```

**変更点（v0.2.0）**:

- `ensure_single_vector()`を使用して、クエリの埋め込み結果を明示的に単一ベクトルに変換
- コードの重複を削減（以前は型チェックロジックがインライン実装）
- 型安全性の向上

## エラー仕様

- `ValidationError`: 空クエリ、top_k<=0、min_scoreが範囲外
- `EmbeddingError`: 埋め込み生成失敗
- `ChromaDBError`: クエリ実行失敗
- その他例外: `error_type` にクラス名を入れて返却

## パフォーマンス/制限

- `top_k` は適切な上限を設けることを推奨（例: 50）
- document プレビューは最大500文字に制限
- 将来的に `where_document` や前処理キャッシュの導入余地あり

## 変更履歴

### v0.2.0 (2025-11-03)

- **改善**: `ensure_single_vector()`ヘルパー関数を使用
  - クエリの埋め込み結果を明示的に単一ベクトルに変換
  - コードの重複削減（約10行削減）
  - 型安全性の向上
- **改善**: インポートに`ensure_single_vector`を追加

### v0.1.0 (初回リリース)

- **実装**: `search()`関数の基本機能
- **実装**: セマンティック検索
- **実装**: フィルタリング機能（file_type, filepath_prefix, min_score）
- **実装**: エラーハンドリング

## 備考

- Chroma の距離（cosine）は `1.0 - distance` で類似度に変換
- `filepath_prefix` は Chroma の where では表現しづらいため取得後フィルタで対応
