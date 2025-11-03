# Semche

ベクトル検索機能を提供するMCPサーバー

## 概要

本プロジェクトは、LangChainとChromaDBを使用したベクトル検索機能を持つModel Context Protocol (MCP) サーバーです。テキスト埋め込み機能とベクトルストレージを提供し、セマンティック検索アプリケーションに利用できます。

## 機能

- **MCPサーバー**: Model Context Protocolの実装
- **テキスト埋め込み**: sentence-transformers/stsb-xlm-r-multilingualを使用して、テキストを768次元ベクトルに変換
- **ベクトルストレージ**: メタデータ（filepath、updated_at、file_type）とともにベクトルをChromaDBに永続化
- **Upsert対応**: 同じfilepathで保存する場合、既存ドキュメントを自動更新
- **Helloツール**: テスト用の簡易挨拶ツール（"Hello, {name}!"を返す）

## 必要要件

- Python 3.10以上
- uv（パッケージ管理用）

## インストール

1. リポジトリをクローン:

```bash
git clone https://github.com/paterapatera/semche.git
cd semche
```

2. uvを使って依存関係をインストール:

```bash
uv sync
```

3. 開発用依存関係をインストール（MCP Inspectorを含む）:

```bash
uv sync --extra dev
```

## 使用方法

### MCPサーバーの起動

uvを使ってサーバーを起動:

```bash
uv run python src/semche/mcp_server.py
```

サーバーが起動し、stdioでMCPプロトコルメッセージを待ち受けます。

### MCP Inspectorでのテスト

MCP Inspectorを使ってサーバーをテスト:

```bash
uv run mcp dev src/semche/mcp_server.py
```

インタラクティブなインスペクターが起動し、以下が可能です:

1. 利用可能なツールの表示
2. 異なるパラメータで`hello`ツールを呼び出し
3. レスポンスの確認

MCP Inspectorでの使用例:

- パラメータなしで`hello`を呼び出し: "Hello, World!"を返す
- 名前"Alice"で`hello`を呼び出し: "Hello, Alice!"を返す

### テストの実行

pytestを使ってテストスイートを実行:

```bash
uv run pytest
```

カバレッジ付きでテストを実行:

```bash
uv run pytest --cov=semche --cov-report=html
```

### コード品質チェック

#### Lint（Ruff）

ruffを使ってコードスタイルとインポート順序をチェック:

```bash
uv run ruff check .
```

自動修正可能な問題を修正:

```bash
uv run ruff check --fix .
```

フォーマットをチェック:

```bash
uv run ruff format --check .
```

自動フォーマット:

```bash
uv run ruff format .
```

#### 型チェック（mypy）

mypyを使って型アノテーションをチェック:

```bash
uv run mypy src/semche
```

特定のファイルをチェック:

```bash
uv run mypy src/semche/mcp_server.py
```

## プロジェクト構成

```
/home/pater/semche/
├── src/
│   └── semche/
│       ├── __init__.py
│       ├── mcp_server.py           # MCPサーバー実装
│       ├── tools/                   # ツール実装（サーバーから委譲）
│       │   ├── __init__.py
│       │   ├── hello.py             # helloツール
│       │   ├── hello.py.exp.md      # helloツール詳細設計
│       │   ├── document.py          # put_documentツール
│       │   ├── document.py.exp.md   # put_documentツール詳細設計
│       │   ├── search.py            # searchツール
│       │   └── search.py.exp.md     # searchツール詳細設計
│       ├── embedding.py            # テキスト埋め込み機能
│       ├── embedding.py.exp.md     # 埋め込みモジュール詳細設計書
│       ├── chromadb_manager.py     # ChromaDBストレージマネージャー
│       └── chromadb_manager.py.exp.md  # ChromaDBモジュール詳細設計書
├── tests/
│   ├── __init__.py
│   ├── test_mcp_server.py          # MCPサーバーのテスト
│   ├── test_embedding.py           # 埋め込み機能のテスト
│   └── test_chromadb_manager.py    # ChromaDBマネージャーのテスト
├── story/                          # 機能ストーリーと要件
├── pyproject.toml                  # プロジェクト設定
├── README.md                       # このファイル
├── AGENTS.md                       # 開発ガイドライン
└── .gitignore                      # Git除外パターン
```

## 利用可能なツール

### hello

挨拶メッセージを返します。

**パラメータ:**

- `name` (string, オプション): 挨拶する名前。デフォルトは"World"。

**返却値:**

- "Hello, {name}!"形式の挨拶メッセージ

**例:**

```json
{
  "name": "hello",
  "arguments": {
    "name": "Alice"
  }
}
```

**レスポンス:**

```
Hello, Alice!
```

### put_document

テキストをベクトル化してChromaDBに保存します（upsert）。同じfilepathで呼び出すと既存ドキュメントを更新します。

**パラメータ:**

- `text` (string, 必須): 登録するテキスト
- `filepath` (string, 必須): ドキュメントの識別子となるファイルパス
- `file_type` (string, オプション): ファイルタイプ（例: "spec", "jira", "design"）
- `normalize` (boolean, オプション): ベクトル正規化を行うか（デフォルト: false）

**返却値:**

- 辞書（dict）形式の結果（成功時は詳細情報、失敗時はエラー情報）

**例:**

```json
{
  "name": "put_document",
  "arguments": {
    "text": "これは仕様書のサンプルテキストです。",
    "filepath": "/docs/spec.md",
    "file_type": "spec",
    "normalize": false
  }
}
```

**レスポンス（成功時）:**

```json
{
  "status": "success",
  "message": "ドキュメントを登録しました",
  "details": {
    "count": 1,
    "collection": "documents",
    "filepath": "/docs/spec.md",
    "vector_dimension": 768,
    "persist_directory": "./chroma_db",
    "normalized": false
  }
}
```

**レスポンス（エラー時）:**

```json
{
  "status": "error",
  "message": "テキストが空です",
  "error_type": "ValidationError"
}
```

### search

クエリ文字列に対するセマンティック検索を実行し、類似ドキュメントを上位`top_k`件返します。

**パラメータ:**

- `query` (string, 必須): 検索クエリ
- `top_k` (number, オプション): 取得件数（デフォルト: 5）
- `file_type` (string, オプション): メタデータの file_type でフィルタ
- `filepath_prefix` (string, オプション): 取得後にパスの接頭辞でフィルタ
- `normalize` (boolean, オプション): クエリベクトルの正規化（デフォルト: false）
- `min_score` (number, オプション): 類似度の下限（0.0〜1.0）
- `include_documents` (boolean, オプション): 本文プレビューを含める（デフォルト: true）

**返却値:**

- 辞書（dict）形式の結果
  - `status`, `message`, `results`（`[{ filepath, score, document?, metadata }]`）, `count`, `query_vector_dimension`, `persist_directory`

**例:**

```json
{
  "name": "search",
  "arguments": {
    "query": "ペット",
    "top_k": 3,
    "file_type": "animal",
    "include_documents": false
  }
}
```

**レスポンス（成功時）:**

```json
{
  "status": "success",
  "message": "検索が完了しました",
  "results": [
    {
      "filepath": "/docs/dog.txt",
      "score": 0.79,
      "metadata": { "file_type": "animal", "updated_at": "2025-11-03T12:00:00" }
    }
  ],
  "count": 1,
  "query_vector_dimension": 768,
  "persist_directory": "./chroma_db"
}
```

## コアモジュール

### Embedder (embedding.py)

sentence-transformersを使用してテキストをベクトル埋め込みに変換します。

```python
from src.semche.embedding import Embedder

embedder = Embedder()
vector = embedder.addDocument("これはテストです。")  # 768次元ベクトルを返す
```

### ChromaDBManager (chromadb_manager.py)

メタデータ付きでChromaDBにベクトルを保存・管理します。

```python
from src.semche.chromadb_manager import ChromaDBManager

mgr = ChromaDBManager(persist_directory="./chroma_db")
result = mgr.save(
    embeddings=[[0.1, 0.2, ...]],
    documents=["仕様書"],
    filepaths=["/docs/spec.md"],
    updated_at=["2025-11-03T12:00:00"],
    file_types=["spec"]
)
```

## 開発

### 新しいツールの追加

新しいツールを追加するには:

1. `src/semche/tools/` に新規ファイルを追加し、FastMCPの `@mcp.tool()` で公開
2. 型ヒントとdocstringを整備し、READMEのツール一覧にパラメータ・返却値を追記
3. `tests/test_mcp_server.py` にテストを追加

### 今後の拡張予定

- ベクトル類似度検索機能
- 埋め込みと保存のMCPツール統合
- バッチ処理機能

## ライセンス

TBD

## コントリビューション

TBD
