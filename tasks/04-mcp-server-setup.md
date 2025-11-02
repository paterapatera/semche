# タスク4: MCPサーバーの基本セットアップ

## 目的

Model Context Protocol (MCP) サーバーの基礎構造を構築し、Cursor IDEとの接続を確立する

## 作業内容

### 1. MCPサーバーのメインファイル作成

```typescript
// src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { logger } from "./utils/logger.js";
import { config } from "./config.js";
import { getVectorStore, closeVectorStore } from "./utils/vectorStore.js";

// サーバーインスタンスの作成
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

/**
 * ツール一覧のハンドラー
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  logger.info("Listing available tools");

  return {
    tools: [
      {
        name: "indexDocuments",
        description:
          "Index or update documents in the vector store. Supports upsert operations.",
        inputSchema: {
          type: "object",
          properties: {
            documents: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  content: {
                    type: "string",
                    description: "Document content to index",
                  },
                  metadata: {
                    type: "object",
                    description: "Document metadata (filePath, language, etc.)",
                    properties: {
                      filePath: { type: "string" },
                      language: { type: "string" },
                      projectName: { type: "string" },
                    },
                  },
                  id: {
                    type: "string",
                    description: "Unique document ID (optional)",
                  },
                },
                required: ["content"],
              },
              description: "Array of documents to index",
            },
            upsert: {
              type: "boolean",
              description:
                "If true, update existing documents with same ID (default: true)",
              default: true,
            },
          },
          required: ["documents"],
        },
      },
      {
        name: "search",
        description: "Search for similar documents using semantic search",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query text",
            },
            k: {
              type: "number",
              description: "Number of results to return (default: 5)",
              default: 5,
            },
            filter: {
              type: "object",
              description:
                "Metadata filter (e.g., {filePath: '/path/to/file.ts'})",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "deleteDocuments",
        description: "Delete documents from the vector store",
        inputSchema: {
          type: "object",
          properties: {
            ids: {
              type: "array",
              items: { type: "string" },
              description: "Array of document IDs to delete",
            },
            filter: {
              type: "object",
              description:
                "Delete all documents matching filter (e.g., {filePath: '/path'})",
            },
          },
        },
      },
      {
        name: "getCollectionInfo",
        description:
          "Get information about the current vector store collection",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
    ],
  };
});

/**
 * ツール呼び出しハンドラー（現時点では未実装）
 */
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

/**
 * リソース一覧のハンドラー（現時点では空）
 */
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  logger.info("Listing available resources");

  return {
    resources: [],
  };
});

/**
 * プロンプト一覧のハンドラー（現時点では空）
 */
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  logger.info("Listing available prompts");

  return {
    prompts: [],
  };
});

/**
 * サーバー起動
 */
async function main() {
  logger.info("Starting Semche MCP Server...");
  logger.info(`Collection: ${config.collectionName}`);
  logger.info(`Persist Directory: ${config.persistDirectory}`);

  // ベクトルストアの初期化（接続確認）
  try {
    await getVectorStore();
    logger.info("Vector store initialized successfully");
  } catch (error) {
    logger.error("Failed to initialize vector store", error);
    throw error;
  }

  // stdioトランスポートでサーバー起動
  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info("Semche MCP Server is running");

  // グレースフルシャットダウン
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
}

// エラーハンドリング付きで起動
main().catch((error) => {
  logger.error("Fatal error", error);
  process.exit(1);
});
```

### 2. package.jsonのスクリプト更新

```json
{
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/index.ts",
    "start": "node dist/index.js",
    "test": "jest",
    "watch": "tsc --watch"
  }
}
```

### 3. 開発環境での動作確認

ターミナルで以下のコマンドを実行:

```bash
# 開発モードで起動
npm run dev
```

期待される出力:

```
[2024-01-01T00:00:00.000Z] [INFO] Starting Semche MCP Server...
[2024-01-01T00:00:00.000Z] [INFO] Collection: semche-collection
[2024-01-01T00:00:00.000Z] [INFO] Persist Directory: ./data/chroma
[2024-01-01T00:00:00.000Z] [INFO] Loading embedding model: sentence-transformers/stsb-xlm-r-multilingual
[2024-01-01T00:00:00.000Z] [INFO] Vector store initialized successfully
[2024-01-01T00:00:00.000Z] [INFO] Semche MCP Server is running
```

### 4. Cursor IDEでの接続設定

Cursor IDE設定ファイル (`.cursor/mcp.json`) を作成:

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

または開発モード用:

```json
{
  "mcpServers": {
    "semche": {
      "command": "npm",
      "args": ["run", "dev"],
      "cwd": "/home/pater/semche"
    }
  }
}
```

## 完了条件

- [ ] src/index.tsが実装されている
- [ ] MCPサーバーが起動する
- [ ] ListToolsRequestが正しく応答する（4つのツールが表示される）
- [ ] ベクトルストアが正常に初期化される
- [ ] グレースフルシャットダウンが機能する
- [ ] Cursor IDEから接続できる（MCP設定後）

## 動作確認方法

### ローカルでの確認

```bash
# ビルド
npm run build

# 起動
npm run start
```

### Cursor IDEでの確認

1. Cursor IDEを再起動
2. MCP設定を確認（設定 > MCP）
3. チャットで「利用可能なツールは？」と質問
4. semcheの4つのツールが表示されることを確認

## トラブルシューティング

- サーバーが起動しない: .envファイルを確認
- Cursor IDEで認識されない: .cursor/mcp.jsonのパスを確認
- 埋め込みモデルエラー: インターネット接続を確認（初回ダウンロード時）

## 次のタスク

タスク5: indexDocumentsツールの実装
