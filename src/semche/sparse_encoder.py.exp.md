````markdown
# sparse_encoder.py 詳細設計書

## 概要

`BM25SparseEncoder` は rank-bm25 の `BM25Okapi` を用いたスパース（キーワード）検索モジュールです。日本語テキストには MeCab + unidic-lite による形態素解析トークナイザをデフォルトで使用し、英語などの空白区切り言語にも対応します。インデックスの保存/読み込み（pickle + json）にも対応します。

ハイブリッド検索（`HybridRetriever`）で Sparse 側のスコア計算に使用されます。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/sparse_encoder.py`
- 依存: 外部ライブラリ `rank-bm25`
- テスト: `/home/pater/semche/tests/test_sparse_encoder.py`

## 利用クラス・ライブラリ（ファイルパス一覧）

- 外部: `rank_bm25.BM25Okapi`
- 外部: `MeCab` (mecab-python3) - 日本語形態素解析（オプショナル）
- 外部: `unidic_lite` - MeCab用軽量辞書（オプショナル）
- 標準: `json`, `pickle`, `pathlib.Path`, `logging`, `typing`

## クラス仕様

### `SparseEncoderError(Exception)`

- スパースエンコーダのエラー用例外

### `BM25SparseEncoder`

```python
class BM25SparseEncoder:
    def __init__(self, tokenizer: Optional[Any] = None)
    def build_index(self, documents: Sequence[str], doc_ids: Sequence[str]) -> dict
    def search(self, query: str, top_k: int = 5) -> list[dict]
    def save(self, directory: str) -> dict
    def load(self, directory: str) -> dict
    def add_documents(self, documents: Sequence[str], doc_ids: Sequence[str]) -> dict
```

#### 属性

- `tokenizer`: トークナイザ関数（`text -> List[str]`）。省略時はデフォルト動作：
  - MeCab + unidic-lite が必須（日本語形態素解析）
  - MeCab 未インストール時は `SparseEncoderError` を送出
  - カスタムトークナイザを渡すことで MeCab 要件を回避可能
- `bm25`: `BM25Okapi | None`（インデックス構築前は None）
- `corpus_texts`: コーパスの元テキスト配列
- `corpus_ids`: テキストに対応する ID 配列

#### `build_index()`

- 入力検証: 文書と ID のリスト長一致、非空
- 手順: トークナイズ -> `BM25Okapi` 構築 -> コーパス保持
- 返却: `{status, count, message}`

#### `search()`

- 前提: `bm25` が初期化済み
- 手順: クエリトークナイズ -> `get_scores()` -> 上位 `top_k` をスコア降順で返却
- 返却: `[{id, text, score}, ...]`

#### `save()` / `load()`

- `save()`: `bm25_index.pkl`（pickle）と `bm25_metadata.json`（テキスト/ID）を保存
- `load()`: 上記 2 ファイルを読み込み復元

#### `add_documents()`

- 既存コーパスに追記して再構築（`build_index()` を内部で再実行）

## 設計上の注意

- **日本語対応（必須）**: MeCab (mecab-python3) + unidic-lite が必須
  - 日本語: 「私は猫が好きです」→ `["私", "は", "猫", "が", "好き", "です"]`
  - MeCab 未インストール時はエラー（`SparseEncoderError`）を送出
  - カスタムトークナイザを渡すことでMeCab要件を回避可能
- BM25 は語彙一致に強いが、意味的類似性は扱わないため Dense 検索と組み合わせる（`HybridRetriever`）
- 永続化ファイルは小規模用途を想定（大量データは専用インデクサの検討余地）

## 変更履歴

### v0.4.1 (2025-11-04)

- **追加**: MeCab + unidic-lite による日本語形態素解析トークナイザをデフォルトで使用
- **改善**: MeCab 未インストール時は警告を表示し、シンプルトークナイザにフォールバック
- **依存**: `mecab-python3>=1.0.6`, `unidic-lite>=1.0.8` を追加

### v0.4.0 (2025-11-03)

- 初版実装: BM25 インデックスの構築/検索/永続化/復元/追加に対応
````
