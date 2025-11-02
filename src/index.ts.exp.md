# index.ts - コード説明ドキュメント

## 概要

このファイルは、Semche MCPサーバーのエントリポイントです。Model Context Protocol (MCP) に準拠したサーバーを実装し、Cursor IDEなどのクライアントとstdio経由で通信します。ベクトルストアを使用したセマンティック検索機能を提供します。

## 依存クラス・モジュール一覧

| クラス/モジュール            | インポート元                                | ファイルパス                                                  | 説明                               |
| ---------------------------- | ------------------------------------------- | ------------------------------------------------------------- | ---------------------------------- |
| `Server`                     | `@modelcontextprotocol/sdk/server/index.js` | `node_modules/@modelcontextprotocol/sdk/dist/server/index.js` | MCPサーバーのコアクラス            |
| `StdioServerTransport`       | `@modelcontextprotocol/sdk/server/stdio.js` | `node_modules/@modelcontextprotocol/sdk/dist/server/stdio.js` | 標準入出力トランスポート           |
| `CallToolRequestSchema`      | `@modelcontextprotocol/sdk/types.js`        | `node_modules/@modelcontextprotocol/sdk/dist/types.js`        | ツール呼び出しリクエストスキーマ   |
| `ListToolsRequestSchema`     | `@modelcontextprotocol/sdk/types.js`        | `node_modules/@modelcontextprotocol/sdk/dist/types.js`        | ツール一覧リクエストスキーマ       |
| `ListResourcesRequestSchema` | `@modelcontextprotocol/sdk/types.js`        | `node_modules/@modelcontextprotocol/sdk/dist/types.js`        | リソース一覧リクエストスキーマ     |
| `ReadResourceRequestSchema`  | `@modelcontextprotocol/sdk/types.js`        | `node_modules/@modelcontextprotocol/sdk/dist/types.js`        | リソース読み込みリクエストスキーマ |
| `ListPromptsRequestSchema`   | `@modelcontextprotocol/sdk/types.js`        | `node_modules/@modelcontextprotocol/sdk/dist/types.js`        | プロンプト一覧リクエストスキーマ   |
| `GetPromptRequestSchema`     | `@modelcontextprotocol/sdk/types.js`        | `node_modules/@modelcontextprotocol/sdk/dist/types.js`        | プロンプト取得リクエストスキーマ   |
| `logger`                     | `./utils/logger.js`                         | `src/utils/logger.ts`                                         | ロギングユーティリティ             |
| `config`                     | `./config.js`                               | `src/config.ts`                                               | アプリケーション設定               |
| `validateConfig`             | `./config.js`                               | `src/config.ts`                                               | 設定検証関数                       |
| `getVectorStore`             | `./utils/vectorStore.js`                    | `src/utils/vectorStore.ts`                                    | ベクトルストア取得関数             |
| `closeVectorStore`           | `./utils/vectorStore.js`                    | `src/utils/vectorStore.ts`                                    | ベクトルストアクローズ関数         |

## サーバーインスタンス

### server

```typescript
const server = new Server(
  {
    name: "semche",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);
```

MCPサーバーのメインインスタンスです。

**設定:**

- **name**: `"semche"` - サーバー名
- **version**: `"1.0.0"` - バージョン番号
- **capabilities**: サーバーが提供する機能
  - `tools`: ツール機能を提供
  - `resources`: リソース機能を提供（今後実装予定）
  - `prompts`: プロンプト機能を提供（今後実装予定）

## リクエストハンドラー

### 1. ListToolsRequestSchema ハンドラー

ツール一覧を返すハンドラーです。

**実装されているツール:**

#### indexDocuments

ドキュメントをベクトルストアにインデックス化します。

**パラメータスキーマ:**

```typescript
{
  type: "object",
  properties: {
    documents: {
      type: "array",
      items: {
        type: "object",
        properties: {
          content: { type: "string" },
          metadata: {
            type: "object",
            properties: {
              filePath: { type: "string" },
              language: { type: "string" },
              projectName: { type: "string" }
            }
          },
          id: { type: "string" }
        },
        required: ["content"]
      }
    },
    upsert: {
      type: "boolean",
      default: true
    }
  },
  required: ["documents"]
}
```

**使用例:**

```json
{
  "documents": [
    {
      "content": "function hello() { return 'world'; }",
      "metadata": {
        "filePath": "/path/to/file.ts",
        "language": "typescript"
      },
      "id": "doc-1"
    }
  ],
  "upsert": true
}
```

#### search

セマンティック検索を実行します。

**パラメータスキーマ:**

```typescript
{
  type: "object",
  properties: {
    query: { type: "string" },
    k: { type: "number", default: 5 },
    filter: { type: "object" }
  },
  required: ["query"]
}
```

**使用例:**

```json
{
  "query": "ログイン機能の実装",
  "k": 10,
  "filter": {
    "language": "typescript"
  }
}
```

#### deleteDocuments

ドキュメントをベクトルストアから削除します。

**パラメータスキーマ:**

```typescript
{
  type: "object",
  properties: {
    ids: {
      type: "array",
      items: { type: "string" }
    },
    filter: { type: "object" }
  }
}
```

**使用例:**

```json
{
  "ids": ["doc-1", "doc-2"]
}
```

または

```json
{
  "filter": {
    "filePath": "/old/project"
  }
}
```

#### getCollectionInfo

コレクション情報を取得します。

**パラメータスキーマ:**

```typescript
{
  type: "object",
  properties: {}
}
```

パラメータは不要です。

### 2. CallToolRequestSchema ハンドラー

ツールの実際の呼び出しを処理します。

**現在の実装:**

```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  logger.info(`Tool called: ${name}`, args);

  // TODO: タスク5以降で各ツールの実装を追加

  return {
    content: [
      {
        type: "text",
        text: `Tool ${name} called successfully (not yet implemented)`,
      },
    ],
  };
});
```

**状態:** 🔨 スタブ実装（実際の処理は未実装）

**今後の実装予定:**

- タスク5: indexDocumentsの実装
- タスク6: searchの実装
- タスク7: deleteDocumentsの実装
- タスク8: getCollectionInfoの実装

### 3. ListResourcesRequestSchema ハンドラー

リソース一覧を返します。

**現在の実装:**

```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  logger.info("Listing available resources");

  return {
    resources: [],
  };
});
```

**状態:** 🔨 空の実装（リソース機能は今後実装予定）

### 4. ListPromptsRequestSchema ハンドラー

プロンプト一覧を返します。

**現在の実装:**

```typescript
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  logger.info("Listing available prompts");

  return {
    prompts: [],
  };
});
```

**状態:** 🔨 空の実装（プロンプト機能は今後実装予定）

## メイン関数

### main()

サーバーの初期化と起動を行います。

**処理フロー:**

```
1. 起動ログ出力
   ↓
2. 設定情報のログ出力
   ↓
3. 設定の検証（validateConfig）
   ↓
4. ベクトルストアの初期化
   ↓
5. stdioトランスポートの作成
   ↓
6. サーバー接続
   ↓
7. 起動完了ログ
   ↓
8. シグナルハンドラー設定
```

**詳細な実装:**

#### 1. 起動ログ

```typescript
logger.info("Starting Semche MCP Server...");
logger.info(`Collection: ${config.collectionName}`);
logger.info(`Persist Directory: ${config.persistDirectory}`);
```

サーバー起動時に基本情報をログ出力します。

#### 2. 設定の検証

```typescript
try {
  validateConfig();
} catch (error) {
  logger.error("Configuration validation failed", error);
  throw error;
}
```

`.env`ファイルの設定が正しいかチェックします。

**検証項目:**

- `persistDirectory`が設定されているか
- `collectionName`が設定されているか
- `embeddingDimension`が正の数か
- `hnswSpace`が`"cosine"`, `"l2"`, `"ip"`のいずれかか

#### 3. ベクトルストアの初期化

```typescript
try {
  await getVectorStore();
  logger.info("Vector store initialized successfully");
} catch (error) {
  logger.error("Failed to initialize vector store", error);
  throw error;
}
```

ChromaDBベクトルストアと埋め込みモデルを初期化します。

**初期化内容:**

- データディレクトリの作成（存在しない場合）
- HuggingFace埋め込みモデルのロード（初回は約400MBダウンロード）
- ChromaDBコレクションの作成/接続

#### 4. トランスポート接続

```typescript
const transport = new StdioServerTransport();
await server.connect(transport);
```

標準入出力（stdio）を使用してMCPクライアントと通信します。

**stdioの役割:**

- `stdin`: クライアントからのリクエスト受信
- `stdout`: クライアントへのレスポンス送信
- `stderr`: ログ出力（MCPプロトコルと干渉しない）

#### 5. グレースフルシャットダウン

```typescript
process.on("SIGINT", async () => {
  logger.info("Shutting down server...");
  await closeVectorStore();
  await server.close();
  process.exit(0);
});

process.on("SIGTERM", async () => {
  logger.info("Shutting down server...");
  await closeVectorStore();
  await server.close();
  process.exit(0);
});
```

**シグナルハンドラー:**

- `SIGINT`: Ctrl+Cによる中断
- `SIGTERM`: システムからの終了要求

**シャットダウン処理:**

1. ベクトルストアのクリーンアップ
2. サーバー接続のクローズ
3. プロセスの終了

## エラーハンドリング

### トップレベルエラーキャッチ

```typescript
main().catch((error) => {
  logger.error("Fatal error", error);
  process.exit(1);
});
```

`main()`関数内で発生した未処理エラーをキャッチし、ログ出力後に終了します。

**終了コード:**

- `0`: 正常終了（SIGINT/SIGTERM）
- `1`: 異常終了（エラー発生）

### エラーの種類

| エラー                            | 原因                 | 対処法                     |
| --------------------------------- | -------------------- | -------------------------- |
| Configuration validation failed   | `.env`の設定が不正   | `.env.example`を参考に修正 |
| Failed to initialize vector store | ChromaDB初期化失敗   | ディスク容量、権限を確認   |
| Model download failed             | 埋め込みモデルDL失敗 | インターネット接続を確認   |

## MCPプロトコルの流れ

### 1. サーバー起動

```bash
node dist/index.js
```

### 2. クライアント接続

Cursor IDEなどがstdio経由で接続します。

### 3. ツール一覧の取得

**クライアント → サーバー:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**サーバー → クライアント:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      { "name": "indexDocuments", ... },
      { "name": "search", ... },
      { "name": "deleteDocuments", ... },
      { "name": "getCollectionInfo", ... }
    ]
  }
}
```

### 4. ツールの呼び出し

**クライアント → サーバー:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "query": "ログイン機能",
      "k": 5
    }
  }
}
```

**サーバー → クライアント:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool search called successfully (not yet implemented)"
      }
    ]
  }
}
```

## 設計上の重要ポイント

### 1. stdioトランスポート

**なぜstdioを使うか:**

- シンプルで軽量
- ファイアウォールやネットワーク設定不要
- セキュリティリスクが低い（ローカル通信のみ）
- Cursor IDEなどのIDEが標準サポート

**制約:**

- ログは必ず`stderr`に出力（`stdout`はプロトコル通信専用）
- バイナリデータの送受信には向かない（JSONベース）

### 2. 非同期処理

すべてのハンドラーとメイン関数は`async`です。

**理由:**

- ベクトルストアの操作は非同期（I/O待機）
- 埋め込みモデルの推論は時間がかかる
- ブロッキングを避けてレスポンシブに

### 3. シングルトンパターン

ベクトルストアはシングルトンで管理されます。

**利点:**

- メモリ効率的（モデルは1回だけロード）
- 状態の一貫性
- 複数リクエスト間でキャッシュ共有

### 4. グレースフルシャットダウン

シグナルハンドラーでクリーンアップを実行します。

**重要性:**

- ベクトルストアの保存処理完了
- リソースリークの防止
- クライアントへの適切な切断通知

## パフォーマンス考慮事項

### 起動時間

| 処理           | 時間   | 備考                 |
| -------------- | ------ | -------------------- |
| 設定読み込み   | <1ms   | 即座                 |
| 設定検証       | <1ms   | 即座                 |
| モデルロード   | 5-10秒 | 初回のみダウンロード |
| ChromaDB初期化 | <1秒   | ローカルDB           |
| サーバー接続   | <100ms | stdio接続            |

**合計:** 約6-11秒（初回）、約1秒（2回目以降）

### メモリ使用量

| コンポーネント    | メモリ                       |
| ----------------- | ---------------------------- |
| Node.jsランタイム | 約50MB                       |
| MCPサーバー       | 約10MB                       |
| 埋め込みモデル    | 約400MB                      |
| ChromaDB          | 約100MB + インデックスサイズ |

**合計:** 約560MB + データサイズ

### 最適化のヒント

```typescript
// ✅ 推奨: ベクトルストアは起動時に1回だけ初期化
await getVectorStore(); // main()で実行

// ❌ 非推奨: リクエストごとに初期化
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  await getVectorStore(); // シングルトンなので大丈夫だが無駄
});
```

## テスト戦略

### ユニットテスト

```typescript
// tests/mcpServer.test.ts
test("should create server instance", () => {
  const server = new Server({ name: "semche", version: "1.0.0" }, ...);
  expect(server).toBeDefined();
});
```

### 統合テスト

```typescript
test("should handle tools/list request", async () => {
  const response = await sendRequest({
    method: "tools/list",
    params: {},
  });
  expect(response.result.tools).toHaveLength(4);
});
```

### E2Eテスト

```bash
# MCPインスペクターで手動テスト
npx @modelcontextprotocol/inspector dist/index.js
```

## トラブルシューティング

### サーバーが起動しない

**症状:**

```
Configuration validation failed
```

**解決策:**

```bash
# .envファイルを確認
cat .env

# 存在しない場合
cp .env.example .env
```

### モデルがロードできない

**症状:**

```
Failed to initialize vector store
Error: Cannot download model
```

**解決策:**

1. インターネット接続を確認
2. プロキシ設定を確認
3. ディスク容量を確認（500MB以上必要）

### Cursor IDEで認識されない

**症状:**
サーバーがMCPリストに表示されない

**解決策:**

1. ビルドを実行: `npm run build`
2. `.cursor/mcp.json`のパスを確認（絶対パス推奨）
3. Cursor IDEを完全に再起動

## 使用箇所

このエントリポイントは以下から呼び出されます:

| 呼び出し元        | 方法                                  | 用途       |
| ----------------- | ------------------------------------- | ---------- |
| `npm run dev`     | `tsx watch src/index.ts`              | 開発モード |
| `npm start`       | `node dist/index.js`                  | 本番モード |
| Cursor IDE        | `.cursor/mcp.json`経由                | IDE統合    |
| MCPインスペクター | `npx @modelcontextprotocol/inspector` | デバッグ   |

## 今後の拡張予定

### タスク5-8: ツール実装

現在スタブのツールを実装します:

- indexDocuments: ドキュメントのインデックス化
- search: セマンティック検索
- deleteDocuments: ドキュメント削除
- getCollectionInfo: 統計情報取得

### タスク9: リソース機能

コレクション情報などをリソースとして公開:

```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "semche://collection/stats",
        name: "Collection Statistics",
        mimeType: "application/json",
      },
    ],
  };
});
```

### タスク10: プロンプト機能

検索用プロンプトテンプレートを提供:

```typescript
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "search-code",
        description: "Search for code snippets",
      },
    ],
  };
});
```

### タスク11: ファイルウォッチャー

ファイルシステムの変更を監視して自動インデックス化:

```typescript
import chokidar from "chokidar";

const watcher = chokidar.watch(config.workspaceRoot);
watcher.on("change", async (path) => {
  // 自動的にインデックス更新
});
```

## まとめ

このMCPサーバーは、Semcheプロジェクトの中核となるコンポーネントです:

- ✅ **MCPプロトコル準拠**: stdio経由でIDEと通信
- ✅ **4つのツール提供**: インデックス化、検索、削除、情報取得
- ✅ **ベクトルストア統合**: セマンティック検索機能
- ✅ **グレースフルシャットダウン**: 安全なクリーンアップ
- ✅ **エラーハンドリング**: 適切なログとエラー報告
- 🔨 **拡張可能**: リソース、プロンプト、ファイルウォッチャー

次のタスクでは、スタブ実装のツールを実際に動作する機能に実装していきます。
