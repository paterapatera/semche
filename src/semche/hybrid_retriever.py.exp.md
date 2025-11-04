````markdown
# hybrid_retriever.py 詳細設計書

## 概要

`HybridRetriever` は Dense（ベクトル検索: Chroma/LangChain）と Sparse（BM25: rank-bm25）の結果を RRF（Reciprocal Rank Fusion）で統合し、ハイブリッド検索を提供するモジュールです。LangChain の API 変化に影響されにくいよう、RRF は本モジュール内で明示実装しています。デフォルトの重みは Dense/Sparse ともに 0.5（50:50）です。

本モジュールは MCP の `search` ツール（`src/semche/tools/search.py`）から使用され、プロジェクトのデフォルト検索をハイブリッド（dense + sparse）に置き換えます。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/hybrid_retriever.py`
- 依存: `/home/pater/semche/src/semche/chromadb_manager.py`, `/home/pater/semche/src/semche/sparse_encoder.py`
- テスト: `tests/test_search.py`（統合）, `tests/test_sparse_encoder.py`（BM25 単体）

## 利用クラス・ライブラリ（ファイルパス一覧）

- `ChromaDBManager`: `/home/pater/semche/src/semche/chromadb_manager.py`
  - 用途: LangChain Chroma ベクトルストア（`vectorstore`）の提供と、BM25 用コーパス取得（`get_all_documents()`）
- `BM25SparseEncoder`: `/home/pater/semche/src/semche/sparse_encoder.py`
  - 用途: スパース（BM25）スコアの計算
- 標準ライブラリ: `logging`, `typing`

## クラス仕様

### `HybridRetrieverError(Exception)`

- ハイブリッド検索中のエラーを表す例外クラス

### `HybridRetriever`

```python
class HybridRetriever:
    def __init__(self, chroma_manager: ChromaDBManager, dense_weight: float = 0.5, sparse_weight: float = 0.5) -> None
    def search(self, query: str, top_k: int = 5, where: dict | None = None, rrf_constant: int = 60) -> list[dict]
```

#### コンストラクタ

- 引数:
  - `chroma_manager`: `ChromaDBManager` インスタンス
  - `dense_weight`: Dense（ベクトル検索）の重み（デフォルト 0.5）
  - `sparse_weight`: Sparse（BM25）の重み（デフォルト 0.5）
- 前提条件: `chroma_manager.vectorstore` が初期化済みであること（埋め込み関数が渡されている）
- 失敗時: `HybridRetrieverError` を送出

#### 内部メソッド `_sparse_scores(query, where, top_k) -> list[dict]`

- `ChromaDBManager.get_all_documents(where, include_documents=True)` で全文とメタデータを取得し、`BM25SparseEncoder` で BM25 スコアを計算。
- 返却: `[{id, score, metadata, document}, ...]` をスコア降順で最大 `top_k` 件

#### `search()` の流れ

1. Dense 検索（LangChain Chroma）
   - `vectorstore.similarity_search_with_relevance_scores(query, k=k*2, filter=where)` を実行
   - rank = 1,2,.. を割り当て、`{id, document, metadata}` を構成（id は `metadata.filepath` 優先）
2. Sparse 検索（BM25）
   - `_sparse_scores(query, where, top_k=k*2)` を実行
   - rank = 1,2,.. を割り当て
3. RRF（Reciprocal Rank Fusion）で統合
   - 定義: `rrf(rank) = 0 if None else 1 / (c + rank)`（c=60）
   - 最終スコア: `dense_weight * rrf(dense_rank) + sparse_weight * rrf(sparse_rank)`
4. スコア降順にソートし、上位 `k` 件を返却

#### 返却フォーマット

- 各要素: `{ "id": str, "document": str | None, "metadata": dict, "score": float }`

## エラー仕様

- `HybridRetrieverError`: vectorstore 未初期化、RRF 統合時の予期せぬエラーなど
- `ChromaDBError`: `ChromaDBManager` 経由の取得で発生したエラー（そのまま再送出）

## 設計上の注意

- LangChain のモジュール構成差異により `EnsembleRetriever` 直接依存は回避し、RRF を自前実装
- BM25 のトークナイザは `sparse_encoder.py` のデフォルト（lowercase + whitespace split）
- `id` は `metadata.filepath` を優先。なければ Chroma の `id` を利用
- メタデータフィルタは Dense/Sparse 両方に適用（`where`）

## 変更履歴

### v0.4.0 (2025-11-03)

- 初版実装: Dense + Sparse（BM25）を RRF で統合するハイブリッド検索を提供
- デフォルト重み: `dense_weight=0.5`, `sparse_weight=0.5`
- RRF 定数 `c=60`
````
