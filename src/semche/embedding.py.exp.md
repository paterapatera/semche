# embedding.py 詳細設計書

## 概要

`embedding.py`は、LangChainとHugging Faceの`sentence-transformers/stsb-xlm-r-multilingual`モデルを使用して、文字列をベクトルデータ（768次元）に変換する機能を提供します。
セマンティック検索機能のためのドキュメント登録機能の前段階として、入力文章を埋め込みモデルでベクトル化し出力します。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/embedding.py`
- テスト: `/home/pater/semche/tests/test_embedding.py`

## 利用クラス・ライブラリ

### 外部ライブラリ

- `langchain_huggingface.HuggingFaceEmbeddings` (langchain-huggingface)
  - ファイルパス: 外部パッケージ (langchain-huggingface)
  - 用途: Hugging Faceの埋め込みモデルをLangChain経由で利用
  - 公式ドキュメント: https://python.langchain.com/docs/integrations/text_embedding/huggingfacehub

### 標準ライブラリ

- `logging`: ログ出力
- `typing`: 型ヒント（List, Union）
- `math`: ベクトル正規化計算

## クラス設計

### EmbeddingError

カスタム例外クラス。埋め込み処理でエラーが発生した際に送出される。

**継承関係:**

- `Exception` を継承

**用途:**

- 空文字列・空リスト入力
- モデルロード失敗
- メモリ不足
- 不正な入力形式

### Embedder

文字列をベクトルデータに変換するメインクラス。

#### コンストラクタ

```python
def __init__(self, model_name: str = "sentence-transformers/stsb-xlm-r-multilingual")
```

**パラメータ:**

- `model_name` (str): 使用する埋め込みモデル名（デフォルト: `sentence-transformers/stsb-xlm-r-multilingual`）

**動作:**

1. `langchain_huggingface`がインストールされているか確認
2. `HuggingFaceEmbeddings`を初期化してモデルをロード
3. 失敗時は`EmbeddingError`を送出

**例外:**

- `EmbeddingError`: モデルロード失敗時、またはlangchain_huggingface未インストール時

#### addDocument メソッド

```python
def addDocument(self, text: Union[str, List[str]], normalize: bool = False) -> Union[List[float], List[List[float]]]
```

**パラメータ:**

- `text` (str | List[str]): 変換する文字列（単一または複数）
- `normalize` (bool): ベクトルをL2正規化するか（デフォルト: False）

**返却値:**

- `List[float]`: 単一文字列の場合、768次元のベクトル
- `List[List[float]]`: 複数文字列の場合、各文字列の768次元ベクトルのリスト

**動作:**

1. 入力検証（空文字列、空リスト、不正な型をチェック）
2. 単一文字列の場合: `embeddings.embed_query(text)` を使用
3. 複数文字列の場合: `embeddings.embed_documents(text)` を使用
4. `normalize=True`の場合、ベクトルをL2正規化
5. エラー時は詳細なログを出力し`EmbeddingError`を送出

**例外:**

- `EmbeddingError`: 以下の場合に送出
  - 空文字列または空リスト
  - 不正な入力形式（str, List[str]以外）
  - メモリ不足
  - その他の埋め込み処理エラー

#### \_normalize メソッド（内部メソッド）

```python
def _normalize(self, vec: List[float]) -> List[float]
```

**パラメータ:**

- `vec` (List[float]): 正規化するベクトル

**返却値:**

- `List[float]`: L2正規化されたベクトル

**動作:**

1. ベクトルのL2ノルムを計算
2. ノルムが0の場合は元のベクトルをそのまま返却
3. 各要素をノルムで除算して正規化

**なぜ正規化が必要か:**

- **類似度計算の最適化**: 正規化されたベクトル同士なら、単純な内積計算だけでコサイン類似度が求められ、計算が高速化されます
- **ベクトルの大きさの影響を排除**: 正規化により「方向（意味）」だけを比較でき、文章の長さなどの影響を受けません
- **検索精度の向上**: 一部のベクトル検索システムでは、正規化されたベクトルを使うことで検索精度が向上する可能性があります

**なぜ必須ではないか:**

- ChromaDBやLangChainは正規化なしでも動作します
- 多くの場合、ライブラリ側で自動的に類似度計算を最適化してくれます
- デフォルトで`normalize=False`としており、通常の用途では明示的な正規化は不要です
- 将来的な最適化オプションとして実装していますが、現時点では省略可能な機能です

## 入出力例

### 単一文字列の変換

```python
from src.semche.embedding import Embedder

embedder = Embedder()
vec = embedder.addDocument("これはテストです。")
print(len(vec))  # 768
print(type(vec))  # <class 'list'>
print(type(vec[0]))  # <class 'float'>
```

### 複数文字列のバッチ変換

```python
embedder = Embedder()
vecs = embedder.addDocument(["テスト1", "テスト2", "テスト3"])
print(len(vecs))  # 3
print(len(vecs[0]))  # 768
```

### 正規化オプション付き変換

```python
embedder = Embedder()
vec = embedder.addDocument("正規化テスト", normalize=True)
norm = sum(x * x for x in vec) ** 0.5
print(norm)  # 1.0 (誤差範囲内)
```

### エラーケース

```python
embedder = Embedder()

# 空文字列
try:
    embedder.addDocument("")
except EmbeddingError as e:
    print(e)  # "空文字列または空リストが入力されました。"

# 空リスト
try:
    embedder.addDocument([])
except EmbeddingError as e:
    print(e)  # "空文字列または空リストが入力されました。"

# 不正な型
try:
    embedder.addDocument(123)
except EmbeddingError as e:
    print(e)  # "不正な入力形式です。strまたはList[str]のみ対応。"
```

## エラー仕様

### EmbeddingError

以下のケースでカスタム例外`EmbeddingError`が送出されます。

| エラーケース                        | エラーメッセージ                                      | ログレベル |
| ----------------------------------- | ----------------------------------------------------- | ---------- |
| langchain_huggingface未インストール | "langchain_huggingfaceがインストールされていません。" | ERROR      |
| モデルロード失敗                    | "モデルのロードに失敗しました: {詳細}"                | ERROR      |
| 空文字列・空リスト                  | "空文字列または空リストが入力されました。"            | ERROR      |
| 不正な入力形式                      | "不正な入力形式です。strまたはList[str]のみ対応。"    | ERROR      |
| メモリ不足                          | "メモリ不足です。入力サイズを減らしてください。"      | ERROR      |
| その他のエラー                      | "埋め込み処理でエラー: {詳細}"                        | ERROR      |

### ログ出力

全てのエラーは`logging.error()`でログ出力され、デバッグ時に詳細を確認できます。

## パフォーマンス特性

- **初回実行**: モデルのダウンロードに時間がかかる（約1-2GB）
- **2回目以降**: キャッシュされたモデルを使用するため高速
- **GPU利用**: PyTorchがGPUを検出すると自動的に利用（CUDA環境）
- **バッチ処理**: 複数文字列を一度に処理することで効率化
- **処理時間**: 単一文字列あたり約0.1-0.5秒（CPU環境）

## テスト

### テストファイル

- `/home/pater/semche/tests/test_embedding.py`

### テストケース

1. **test_single_text_embedding**: 単一文字列の変換
2. **test_batch_text_embedding**: 複数文字列のバッチ変換
3. **test_english_text_embedding**: 英語テキストの変換
4. **test_normalize_option**: 正規化オプションの検証
5. **test_empty_string_error**: 空文字列のエラー検証
6. **test_empty_list_error**: 空リストのエラー検証
7. **test_invalid_input_type**: 不正な入力型のエラー検証

### テスト実行

```bash
uv run pytest tests/test_embedding.py
```

## 今後の拡張予定

- ChromaDBへの保存機能追加（次ストーリー）
- MCPサーバーのツールとして統合
- メタデータ管理機能
- ベクトル検索機能

## 参考資料

- [LangChain HuggingFace Embeddings](https://python.langchain.com/docs/integrations/text_embedding/huggingfacehub)
- [sentence-transformers/stsb-xlm-r-multilingual](https://huggingface.co/sentence-transformers/stsb-xlm-r-multilingual)
- [Sentence Transformers Documentation](https://www.sbert.net/)
