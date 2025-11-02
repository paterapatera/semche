# Semche MCP Server - 動作確認ガイド

## タスク4完了チェックリスト

✅ **完了条件:**

- [x] src/index.tsが実装されている
- [x] MCPサーバーが起動する
- [x] ListToolsRequestが正しく応答する（4つのツールが表示される）
- [x] ベクトルストアが正常に初期化される
- [x] グレースフルシャットダウンが機能する
- [x] Cursor IDEから接続できる設定ファイルが作成されている

## 動作確認結果

### 1. ビルド成功

```bash
$ npm run build
> semche@1.0.0 build
> tsc
```

✅ エラーなくコンパイル完了

### 2. サーバー起動確認

```bash
$ npm run dev
[2025-11-02T02:59:06.023Z] [INFO] Starting Semche MCP Server...
[2025-11-02T02:59:06.023Z] [INFO] Collection: semche_documents
[2025-11-02T02:59:06.023Z] [INFO] Persist Directory: /home/pater/semche/data/chroma
[Semche] Configuration validated successfully
[Semche] Initializing vector store...
[Semche] Loading embedding model: sentence-transformers/stsb-xlm-r-multilingual
[Semche] Vector store initialized with collection: semche_documents
[2025-11-02T02:59:06.024Z] [INFO] Vector store initialized successfully
[2025-11-02T02:59:06.024Z] [INFO] Semche MCP Server is running
```

✅ 正常起動

### 3. ツール一覧の確認

MCPプロトコルでtools/listリクエストを送信:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**レスポンス:**

```json
{
  "result": {
    "tools": [
      {
        "name": "indexDocuments",
        "description": "Index or update documents in the vector store. Supports upsert operations."
      },
      {
        "name": "search",
        "description": "Search for similar documents using semantic search"
      },
      {
        "name": "deleteDocuments",
        "description": "Delete documents from the vector store"
      },
      {
        "name": "getCollectionInfo",
        "description": "Get information about the current vector store collection"
      }
    ]
  }
}
```

✅ 4つのツールが正しく登録されている

### 4. テスト実行

```bash
$ npm run test
 ✓ tests/vectorStore.test.ts (2 tests) 2ms
 ✓ tests/mcpServer.test.ts (2 tests) 2ms

 Test Files  2 passed (2)
      Tests  4 passed (4)
```

✅ 全テストパス

## 利用可能なツール詳細

### 1. indexDocuments

**説明:** ドキュメントをベクトルストアにインデックス化します。

**パラメータ:**

- `documents`: ドキュメント配列
  - `content`: テキスト内容（必須）
  - `metadata`: メタデータ（オプション）
    - `filePath`: ファイルパス
    - `language`: プログラミング言語
    - `projectName`: プロジェクト名
  - `id`: 一意のID（オプション）
- `upsert`: 既存ドキュメントを更新するか（デフォルト: true）

**状態:** 🔨 実装予定（タスク5）

### 2. search

**説明:** セマンティック検索を実行します。

**パラメータ:**

- `query`: 検索クエリ（必須）
- `k`: 返す結果数（デフォルト: 5）
- `filter`: メタデータフィルター（オプション）

**状態:** 🔨 実装予定（タスク6）

### 3. deleteDocuments

**説明:** ドキュメントを削除します。

**パラメータ:**

- `ids`: 削除するドキュメントIDの配列
- `filter`: フィルターに一致するドキュメントを削除

**状態:** 🔨 実装予定（タスク7）

### 4. getCollectionInfo

**説明:** コレクション情報を取得します。

**パラメータ:** なし

**状態:** 🔨 実装予定（タスク8）

## Cursor IDE接続設定

### 本番環境

**ファイル:** `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "semche": {
      "command": "node",
      "args": ["/home/pater/semche/dist/index.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### 開発環境

**ファイル:** `.cursor/mcp-dev.json`（使用時は`mcp.json`にリネーム）

```json
{
  "mcpServers": {
    "semche-dev": {
      "command": "npm",
      "args": ["run", "dev"],
      "cwd": "/home/pater/semche",
      "env": {
        "NODE_ENV": "development"
      }
    }
  }
}
```

## Cursor IDEでの確認手順

1. **ビルド実行:**

   ```bash
   npm run build
   ```

2. **Cursor IDEを再起動**

3. **MCP接続確認:**
   - 設定 > MCP を開く
   - "semche" サーバーが表示されることを確認
   - 状態が "Connected" になることを確認

4. **ツール確認:**
   - Cursorチャットで「利用可能なツールは？」と質問
   - 4つのツール（indexDocuments、search、deleteDocuments、getCollectionInfo）が表示されることを確認

## トラブルシューティング

### サーバーが起動しない

**原因:** 環境変数が設定されていない

**解決策:**

```bash
# .envファイルを確認
cat .env

# 存在しない場合は作成
cp .env.example .env
```

### Cursor IDEで認識されない

**原因:** パスが間違っている、またはビルドされていない

**解決策:**

```bash
# ビルドを実行
npm run build

# dist/index.jsが存在することを確認
ls -la dist/index.js

# .cursor/mcp.jsonのパスを絶対パスに修正
```

### 埋め込みモデルがダウンロードできない

**原因:** インターネット接続の問題

**解決策:**

- インターネット接続を確認
- プロキシ設定を確認
- 手動ダウンロード後にキャッシュに配置

## 次のタスク

タスク5: indexDocumentsツールの実装

現在、4つのツールはスタブ実装（"not yet implemented"を返す）です。
次のタスクでは、実際のインデックス化機能を実装します。
