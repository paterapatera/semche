# search.py 詳細設計書

## 概要

`search` はクエリ文字列に対して Dense（ベクトル）と Sparse（BM25）を組み合わせたハイブリッド検索を実行し、RRF（Reciprocal Rank Fusion）で統合した結果を返すツール関数です。MCP サーバー（`mcp_server.py`）から `@mcp.tool()` で公開されます。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/tools/search.py`
- 呼び出し元: `/home/pater/semche/src/semche/mcp_server.py`
- 設計: `/home/pater/semche/src/semche/tools/search.py.exp.md`
- 依存: `/home/pater/semche/src/semche/hybrid_retriever.py`, `/home/pater/semche/src/semche/chromadb_manager.py`, `/home/pater/semche/src/semche/tools/document.py`
- テスト: `/home/pater/semche/tests/test_search.py`

## 利用クラス・ライブラリ（ファイルパス一覧）

- `HybridRetriever` / `HybridRetrieverError`: `/home/pater/semche/src/semche/hybrid_retriever.py`
- `ChromaDBManager` / `ChromaDBError`: `/home/pater/semche/src/semche/chromadb_manager.py`
- `_get_chromadb_manager`: `/home/pater/semche/src/semche/tools/document.py`（シングルトンの共有）

## 関数仕様

### `search(query: str, top_k: int = 5, file_type: Optional[str] = None, include_documents: bool = True, max_content_length: Optional[int] = None) -> dict`

- 役割: ハイブリッド検索（Dense + Sparse, RRF 統合）を実行し、結果を dict で返却
- 引数:
  - `query`: 検索クエリ文字列（必須, 非空）
  - `top_k`: 上位件数（>=1）
  - `file_type`: メタデータ `file_type` でフィルタ
  - `include_documents`: ドキュメント本文を含めるか
  - `max_content_length`: ドキュメント内容の最大文字数。`None`（デフォルト）の場合は全文取得。整数値を指定した場合はその文字数で切り詰め（`"..."`付加）
- 返り値: `dict`
  - 成功時: `{status, message, results: [{filepath, score, document?, metadata}], count, query_vector_dimension, persist_directory}`（`query_vector_dimension` はハイブリッド移行後は `None`）
  - 失敗時: `{status: "error", message, error_type}`

## 内部処理フロー

```
search(...)
  ├─ バリデーション（query, top_k）
  ├─ where = {file_type?}
  ├─ chroma = _get_chromadb_manager()  # 共有シングルトン
  ├─ retriever = HybridRetriever(chroma, dense_weight=0.5, sparse_weight=0.5)
  ├─ items = retriever.search(query, top_k, where)
  ├─ results = items を整形（max_content_lengthが指定されている場合は文字数制限、Noneの場合は全文）
  └─ dict で返却
```

## エラー仕様

- `ValidationError`: 空クエリ、top_k<=0
- `HybridRetrieverError`: ハイブリッド検索実行失敗
- `ChromaDBError`: ChromaDB 経由の取得失敗
- その他例外: `error_type` にクラス名を入れて返却

## パフォーマンス/制限

- `top_k` は適切な上限を推奨（例: 50）
- document 内容はデフォルトで全文取得。大きなドキュメントの場合は `max_content_length` で制限可能
- RRF の定数は 60（`c=60`）。必要に応じて調整余地あり
- Sparse 側コーパスは都度 `get_all_documents()` から構築しており、大規模データでは専用の永続インデックス管理が望ましい

## 変更履歴

### v0.5.0 (2025-11-06)

- **追加**: `max_content_length` パラメータを追加。`None`（デフォルト）で全文取得、整数値指定で文字数制限
- **変更**: デフォルト動作を500文字制限から全文取得に変更

### v0.4.0 (2025-11-03)

- **変更**: デフォルトの検索をハイブリッド（Dense + Sparse, RRF）に完全移行（後方互換なし）
- **追加**: `HybridRetriever` を利用する実装に置換
- **仕様**: 返却値の `query_vector_dimension` は `None` を返す

### v0.3.0 (2025-11-03)

- セマンティック検索（Dense のみ）版の簡素化

## 備考

- Chroma の類似度スコアは LangChain の `similarity_search_with_relevance_scores` に準拠
- 追加のフィルタリングが必要な場合は、アプリケーション側で実装を推奨
