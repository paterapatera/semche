# ユーザーはMCPで本機能を実行できる

## 概要

本ストーリーでは、MCPサーバーのスケルトンを作成し、単一の`hello`ツールで動作確認を行います。
通信はstdio、パッケージ管理はuv、手動テストはMCP Inspectorを使用します。

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

[x] ストーリーの背景と目的を確認する
[x] 実装する機能の詳細をユーザーと対話して決定する
[x] 技術スタック（uv、FastMCP、pytest、MCP Inspector）をユーザーと相談する
[x] ファイル構成案を提示し、ユーザーの承認を得る
[x] **Phase 1完了の確認をユーザーから得てから次に進む**
[x] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

[x] MCPサーバーの実装が完了している
[x] 機能がMCPツールとして公開されている（helloツール）
[x] エラーハンドリングが適切に実装されている
[x] テストコードが作成されている
[x] テストが全てパスする

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [x] 実装完了を報告し、ユーザーにレビューを依頼する
      [x] 手動での動作確認を行う（MCP Inspectorで確認済み）
- [x] 今回更新したコードの詳細設計書を更新する
- [x] **全ての作業完了をユーザーに報告する**

## Phase 1で確定した内容

- 目的: MCPスケルトン実装と動作確認
- 公開ツール: `hello`（引数 `name: string` | optional、デフォルト "World"）
- 通信方式: stdio
- パッケージ管理: uv
- 構成: `src/semche/mcp_server.py` に FastMCP を用いて実装
- テスト: pytest（ユニットテスト）、MCP Inspector（手動）
- リポジトリ構成: `src` 配下にコード、`tests` 配下にテスト

## 実装内容

### 1. MCPサーバーのセットアップ

- MCPサーバーの基本構造を実装
- 必要な依存関係のインストール
- サーバーの起動・停止機能

### 2. ツールの定義

- 対象ツールは `hello` のみ
- ツール名、説明、パラメータ（`name`: string, optional）の定義
- FastMCP による自動スキーマ生成（型ヒントから）
- 出力は文字列（例: "Hello, Alice!"）

### 3. 実装方針

- FastMCP の `@mcp.tool()` デコレータで同期関数として実装
- エラーハンドリング（無効な引数はFastMCPがバリデーション）
- レスポンスは文字列を返却

### 4. テスト

- 単体テストの作成
- 統合テストの作成
- 手動テストの実施

### 5. ドキュメント

- 使用方法のドキュメント作成
- APIリファレンスの作成
- 詳細設計書の更新

## 技術仕様

- プロトコル: Model Context Protocol (MCP)
- 通信方式: stdio
- データフォーマット: JSON

## 参考資料

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol)
