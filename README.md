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

## プロジェクト構成

```
/home/pater/semche/
├── src/
│   └── semche/
│       ├── __init__.py
│       ├── mcp_server.py           # MCPサーバー実装
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

1. `list_tools()`関数にツール定義を追加
2. `call_tool()`関数にツールロジックを実装
3. `tests/test_mcp_server.py`にテストを追加

### 今後の拡張予定

- ベクトル類似度検索機能
- 埋め込みと保存のMCPツール統合
- バッチ処理機能

## ライセンス

TBD

## コントリビューション

TBD
