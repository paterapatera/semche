# Semche

ベクトル検索機能を提供するMCPサーバー

## 概要

本プロジェクトは、LangChainとChromaDBを使用したベクトル検索機能を持つModel Context Protocol (MCP) サーバーです。テキスト埋め込み機能とベクトルストレージを提供し、セマンティック検索アプリケーションに利用できます。

**v0.3.0の主な機能**:

- LangChainベクトルストア統合による検索機能の改善
- 将来のハイブリッド検索（dense + sparse）への拡張を見据えた設計

## 機能

- **MCPサーバー**: Model Context Protocolの実装
- **テキスト埋め込み**: sentence-transformers/stsb-xlm-r-multilingualを使用して、テキストを768次元ベクトルに変換
- **ベクトルストレージ**: メタデータ（filepath、updated_at、file_type）とともにベクトルをChromaDBに永続化
- **LangChain統合**: LangChain Chromaベクトルストアを使用した検索機能
- **Upsert対応**: 同じfilepathで保存する場合、既存ドキュメントを自動更新

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
2. 異なるパラメータでツールを呼び出し
3. レスポンスの確認

### CLIツール: doc-update

ローカルファイル群を一括でベクトル化し、ChromaDBに登録するCLIツールです。

#### インストール後の起動

```bash
uv sync  # エントリポイントを有効化
doc-update [オプション] [入力パス...]
```

#### 基本的な使用例

```bash
# ディレクトリ配下のMarkdownファイルを登録（デフォルト：絶対パス）
doc-update ./docs/**/*.md --file-type note

# 相対パスで登録
doc-update ./docs/**/*.md --use-relative-path --file-type note

# プレフィックス付きで登録（絶対パス）
doc-update ./project --id-prefix myproject --file-type code
# → /home/user/project/file.md は myproject:/home/user/project/file.md として登録

# 日付フィルタとignoreパターン
doc-update ./wiki --filter-from-date 2025-11-01 --ignore "**/.git/**" --file-type wiki

# ChromaDB保存先を指定
doc-update ./notes --chroma-dir /tmp/chroma --file-type memo
```

#### オプション一覧

- `inputs` (位置引数): ファイル/ディレクトリ/ワイルドカードパターン（複数可）
  - 例: `./docs`, `**/*.md`, `/var/test/**/*.txt`
- `--id-prefix PREFIX`: ドキュメントIDのプレフィックス
  - 指定すると `PREFIX:パス` 形式のIDが生成されます
- `--use-relative-path`: 相対パスでIDを生成（デフォルトは絶対パス）
- `--file-type TYPE`: メタデータのfile_type（デフォルト: `none`）
  - 単一値のみ指定可能（例: `spec`, `note`, `code`）
- `--filter-from-date YYYY-MM-DD`: 指定日時以降に更新されたファイルのみ対象
  - ISO8601形式も可（例: `2025-11-01T12:30:45`）
- `--ignore PATTERN`: 除外パターン（複数回指定可、glob形式）
  - 例: `--ignore "**/.git/**" --ignore "**/node_modules/**"`
- `--chroma-dir DIR`: ChromaDB保存先ディレクトリ
  - 環境変数 `SEMCHE_CHROMA_DIR` より優先されます

#### ID生成ルール

**デフォルト動作（絶対パス）**:

- ファイルの絶対パスをIDとして使用（v0.2.0より）
- `--id-prefix` を指定すると `プレフィックス:絶対パス` 形式
- パスセパレータは `/` に統一（Windows互換性）

**相対パスオプション**:

- `--use-relative-path` を指定すると、実行ディレクトリ（`cwd`）からの相対パスをIDとして使用
- `--id-prefix` と併用可能: `プレフィックス:相対パス` 形式

**例**:

```bash
# 絶対パス（デフォルト）
cd /home/user/project
doc-update docs/file.md
# → ID: /home/user/project/docs/file.md

# 絶対パス + プレフィックス
doc-update docs/file.md --id-prefix myproject
# → ID: myproject:/home/user/project/docs/file.md

# 相対パス
doc-update docs/file.md --use-relative-path
# → ID: docs/file.md

# 相対パス + プレフィックス
doc-update docs/file.md --use-relative-path --id-prefix myproject
# → ID: myproject:docs/file.md
```

**注意**: 絶対パスと相対パスは異なるドキュメントとして扱われます。

#### 処理の流れ

1. 入力パターン（ワイルドカード/ディレクトリ/ファイル）を解決
2. ignoreパターンと日付フィルタを適用
3. ファイル内容をUTF-8で読み込み（バイナリはスキップ）
4. テキストをベクトル化（768次元）
5. ChromaDBに一括保存（upsert: 既存IDは更新）
6. 結果サマリを出力（成功/スキップ件数）

#### ヘルプ表示

```bash
doc-update --help
```

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
│       │   ├── document.py          # put_documentツール
│       │   ├── document.py.exp.md   # put_documentツール詳細設計
│       │   ├── search.py            # searchツール
│       │   ├── search.py.exp.md     # searchツール詳細設計
│       │   ├── delete.py            # delete_documentツール
│       │   └── delete.py.exp.md     # delete_documentツール詳細設計
│       ├── embedding.py            # テキスト埋め込み機能
│       ├── embedding.py.exp.md     # 埋め込みモジュール詳細設計書
│       ├── chromadb_manager.py     # ChromaDBストレージマネージャー
│       └── chromadb_manager.py.exp.md  # ChromaDBモジュール詳細設計書
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # テスト分離のための環境変数設定
│   ├── test_mcp_server.py          # MCPサーバーのテスト
│   ├── test_embedding.py           # 埋め込み機能のテスト
│   ├── test_chromadb_manager.py    # ChromaDBマネージャーのテスト
│   ├── test_search.py              # 検索ツールのテスト
│   ├── test_embedding_helper.py    # ヘルパー関数のテスト
│   └── test_delete.py              # 削除ツールのテスト
├── story/                          # 機能ストーリーと要件
├── pyproject.toml                  # プロジェクト設定
├── README.md                       # このファイル
├── AGENTS.md                       # 開発ガイドライン
└── .gitignore                      # Git除外パターン
```

## 利用可能なツール

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

### delete_document

指定した`filepath`（ID）のドキュメントを削除します。存在しないIDが指定された場合はエラーにせず、`deleted_count=0`として成功レスポンスを返します。

**パラメータ:**

- `filepath` (string, 必須): 削除対象のID（パス）

**返却値:**

- 辞書（dict）形式の結果
  - 成功（削除あり）: `{status: "success", message: "ドキュメントを削除しました", deleted_count: 1, filepath, collection, persist_directory}`
  - 成功（該当なし）: `{status: "success", message: "削除対象が見つかりませんでした", deleted_count: 0, filepath, collection, persist_directory}`
  - 失敗: `{status: "error", message, error_type}`

**例:**

```json
{
  "name": "delete_document",
  "arguments": {
    "filepath": "/docs/spec.md"
  }
}
```

**レスポンス（成功: 削除あり）:**

```json
{
  "status": "success",
  "message": "ドキュメントを削除しました",
  "deleted_count": 1,
  "filepath": "/docs/spec.md",
  "collection": "documents",
  "persist_directory": "./chroma_db"
}
```

**レスポンス（成功: 該当なし）:**

```json
{
  "status": "success",
  "message": "削除対象が見つかりませんでした",
  "deleted_count": 0,
  "filepath": "/docs/not_found.md",
  "collection": "documents",
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

## IDE/Agent 連携（Cursor など）

MCP クライアント（Cursor の Agent など）から本サーバーを使うには、クライアント側の設定ファイル（例: `mcp.json` やクライアントの設定 UI）でサーバーの起動方法を指定します。

MCP の統合方法は大きく2通りあります。

1. STDIO でプロセスを起動して接続（command/args/env を指定）

- クライアントがサーバープロセスを起動し、標準入出力で通信します。
- この方式では command/args は必須、必要に応じて env を設定します。

JSON 設定例（STDIO 方式、開発向け）:

```json
{
  "mcpServers": {
    "semche": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "src/semche/mcp_server.py"],
      "env": {
        "SEMCHE_CHROMA_DIR": "${workspaceFolder}/chroma_db"
      }
    }
  }
}
```

補足:

- `command`/`args` はクライアントが起動するプロセスを指定します。`uv` を使わない場合は `python src/semche/mcp_server.py` 相当を指定してください。
- `env` は任意です。本プロジェクトでは `SEMCHE_CHROMA_DIR` を指定すると ChromaDB の永続ディレクトリを切り替えられます（未指定時は `./chroma_db`）。
- 一部クライアントでは `mcp dev` などの開発用コマンドを `command` に指定できない場合があります。その場合は、純粋にサーバーを STDIO で起動するコマンドを指定してください。

2. HTTP サーバーとして接続（url を指定）

- サーバー側が HTTP エンドポイントを提供している場合は、`url` のみを指定します。
- この方式では `command/args/env` は不要です（クライアントは既に稼働中の HTTP サーバーへ接続）。

JSON 設定例（HTTP 方式）:

```json
{
  "mcpServers": {
    "semche": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

注意:

- 本リポジトリのデフォルトは STDIO 想定です（MCP Inspector の開発体験: `uv run mcp dev src/semche/mcp_server.py`）。HTTP での提供を行う場合は、別途 HTTP ランナーの用意が必要です。
- Cursor/IDE 側の設定キー名（`mcpServers` / `servers` など）はクライアント実装により異なります。ご利用のクライアントのドキュメントに従って読み替えてください。

### よくある質問（FAQ）

- Q: command, args, env の設定は必要？
  - A: STDIO 方式でクライアントからサーバーを起動する場合は必要です。HTTP 方式で既存のエンドポイントへ接続する場合は不要です（`url` のみ）。
- Q: どの環境変数を設定すべき？
  - A: 必須はありませんが、`SEMCHE_CHROMA_DIR` を設定すると ChromaDB の保存先を制御できます。モデルのキャッシュ等を調整したい場合は環境に応じて `TRANSFORMERS_CACHE` や `SENTENCE_TRANSFORMERS_HOME` を設定するとダウンロード先を固定できます。
