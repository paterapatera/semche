# mcp_server.py 詳細設計書

## 概要

このファイルは、Semcheプロジェクトの MCP (Model Context Protocol) サーバーのメイン実装ファイルです。
FastMCP を使用してツールを登録します。実際のツール実装は `src/semche/tools/` 配下に分割されています。

## ファイルパス

`/home/pater/semche/src/semche/mcp_server.py`

## 依存関係

### 外部ライブラリ

- `mcp.server.fastmcp.FastMCP`: MCPサーバーの高レベルAPI

### 内部モジュール

- `semche.tools.hello`: helloツールの実装
- `semche.tools.document.put_document`: ドキュメント登録ツールの実装

### 標準ライブラリ

（本ファイルでは直接使用しません。ツール側で必要に応じて使用します）

### 利用しているクラス・モジュール

| モジュール/クラス | インポート元         | 用途                    |
| ----------------- | -------------------- | ----------------------- |
| `FastMCP`         | `mcp.server.fastmcp` | MCPサーバーの作成と管理 |
| `hello`           | `semche.tools`       | helloツールの委譲先     |
| `put_document`    | `semche.tools`       | 登録ツールの委譲先      |

## グローバル変数とヘルパー関数

### `mcp`

```python
mcp = FastMCP("semche")
```

**型**: `FastMCP`

**説明**: MCPサーバーのインスタンス。サーバー名は "semche" として初期化されます。

本ファイルでは状態を保持しません。必要なシングルトン管理（Embedder/ChromaDBManagerの遅延初期化）は
各ツールモジュール（例: `tools/document.py`）側で行います。

## ツール登録

本サーバーはツールの公開と委譲のみを担います。実装は tools 配下をご参照ください。

- hello: `src/semche/tools/hello.py`（設計: `hello.py.exp.md`）
- put_document: `src/semche/tools/document.py`（設計: `document.py.exp.md`）
- search: `src/semche/tools/search.py`（設計: `search.py.exp.md`）

## データフロー

### データフロー（全体像）

```
MCPクライアント
    ↓ (ツール呼び出し: hello / put_document)
FastMCPサーバー (mcp_server)
    ↓ （引数をそのまま委譲）
tools.* の各実装
    ↓ （処理・レスポンス生成）
FastMCPサーバー (mcp_server)
    ↓
MCPクライアント
```

## エラーハンドリング

詳細なエラーハンドリングは各ツールの実装に委譲します（tools/\*.py参照）。
本サーバーファイルでは FastMCP による一般的なエラー処理に依存します。

## セキュリティ考慮事項

- 入力値のサニタイゼーション: 現在は未実装（将来的に必要に応じて追加）
- 認証: MCP Inspectorのトークンベース認証を使用
- stdio通信: ローカル実行のため、ネットワーク経由の攻撃リスクは低い

## パフォーマンス考慮事項

- 本ファイルは薄い委譲レイヤーのため、状態・重い処理は保持しません
- モデルロードやストレージ接続などの最適化は tools 側で実施します

## テスト

関連テストファイル: `/home/pater/semche/tests/test_mcp_server.py`

テストケースの詳細は `tests/test_mcp_server.py` と各ツールの `.exp.md` を参照してください。

## 使用方法

### 開発モード（MCP Inspector）

```bash
cd /home/pater/semche
uv run mcp dev src/semche/mcp_server.py
```

ブラウザでMCP Inspectorが開き、以下が可能：

- ツール一覧の確認
- インタラクティブなツール呼び出し
- レスポンスの検証

### 本番モード（stdio）

```bash
cd /home/pater/semche
uv run python src/semche/mcp_server.py
```

stdioでMCPプロトコル通信を受け付けます。

## バージョン情報

- 初版作成日: 2025-11-03
- バージョン: 0.1.0
- 最終更新日: 2025-11-03

## 変更履歴

| 日付       | バージョン | 変更内容                                  |
| ---------- | ---------- | ----------------------------------------- |
| 2025-11-03 | 0.1.0      | 初版作成。FastMCPを使用したスケルトン実装 |
