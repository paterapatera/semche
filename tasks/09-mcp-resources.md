# タスク9: MCPリソースの実装

## 目的

MCP (Model Context Protocol) のリソース機能を実装し、Cursor IDEからコレクションの情報をリソースとして参照できるようにする

## 作業内容

### 1. リソースハンドラーの作成

```typescript
// src/resources/index.ts
import {
  getCollectionInfo,
  getLanguageStats,
  getFileStats,
} from "../tools/getCollectionInfo.js";
import { logger } from "../utils/logger.js";
import { config } from "../config.js";

/**
 * collection://stats リソース
 * コレクションの統計情報を返す
 */
export async function getStatsResource(): Promise<string> {
  logger.info("Getting stats resource");

  const result = await getCollectionInfo();
  const langStats = await getLanguageStats();
  const fileStats = await getFileStats();

  let output = "# Semche Vector Store Statistics\n\n";
  output += `## Overview\n\n`;
  output += `- **Collection Name:** ${result.info.collectionName}\n`;
  output += `- **Documents:** ${result.info.documentCount}\n`;
  output += `- **Chunks:** ${result.info.chunkCount}\n`;
  output += `- **Unique Files:** ${result.info.uniqueFiles}\n`;
  output += `- **Storage Size:** ${result.info.storageSize || "N/A"}\n\n`;

  output += `## Language Distribution\n\n`;
  Object.entries(langStats)
    .sort(([, a], [, b]) => b - a)
    .forEach(([lang, count]) => {
      output += `- **${lang}:** ${count} chunks\n`;
    });

  output += `\n## Top Files by Chunks\n\n`;
  fileStats.slice(0, 10).forEach((file, index) => {
    output += `${index + 1}. **${file.filePath}** - ${file.chunks} chunks\n`;
  });

  output += `\n## Recent Documents\n\n`;
  result.info.recentDocuments.forEach((doc, index) => {
    output += `${index + 1}. ${doc.filePath}\n`;
    output += `   - Indexed: ${doc.indexedAt}\n`;
  });

  return output;
}

/**
 * collection://documents リソース
 * インデックスされた全ドキュメントのリストを返す
 */
export async function getDocumentsResource(): Promise<string> {
  logger.info("Getting documents resource");

  const fileStats = await getFileStats();

  let output = "# Indexed Documents\n\n";
  output += `Total files: ${fileStats.length}\n\n`;

  fileStats.forEach((file, index) => {
    output += `${index + 1}. **${file.filePath}**\n`;
    output += `   - Chunks: ${file.chunks}\n`;
  });

  return output;
}

/**
 * collection://config リソース
 * 現在の設定情報を返す
 */
export async function getConfigResource(): Promise<string> {
  logger.info("Getting config resource");

  let output = "# Semche Configuration\n\n";
  output += `## Vector Store Settings\n\n`;
  output += `- **Collection Name:** ${config.collectionName}\n`;
  output += `- **Persist Directory:** ${config.persistDirectory}\n`;
  output += `- **Embedding Model:** ${config.embeddingModel}\n`;
  output += `- **Embedding Dimension:** ${config.embeddingDimension}\n\n`;

  output += `## HNSW Index Settings\n\n`;
  output += `- **Space:** ${config.hnswSpace}\n`;
  output += `- **Construction EF:** ${config.hnswConstructionEf}\n`;
  output += `- **M:** ${config.hnswM}\n\n`;

  output += `## Text Processing\n\n`;
  output += `- **Chunk Size:** ${config.chunkSize}\n`;
  output += `- **Chunk Overlap:** ${config.chunkOverlap}\n\n`;

  if (config.watchEnabled) {
    output += `## File Watching\n\n`;
    output += `- **Enabled:** Yes\n`;
    output += `- **Watch Patterns:** ${config.watchPatterns?.join(", ") || "N/A"}\n`;
    output += `- **Ignore Patterns:** ${config.watchIgnorePatterns?.join(", ") || "N/A"}\n`;
  } else {
    output += `## File Watching\n\n`;
    output += `- **Enabled:** No\n`;
  }

  return output;
}
```

### 2. MCPサーバーへのリソース統合

```typescript
// src/index.ts (ListResourcesRequestSchema と ReadResourceRequestSchema を更新)
import {
  getStatsResource,
  getDocumentsResource,
  getConfigResource,
} from "./resources/index.js";

/**
 * リソース一覧のハンドラー
 */
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  logger.info("Listing available resources");

  return {
    resources: [
      {
        uri: "collection://stats",
        name: "Collection Statistics",
        description:
          "Get statistics about the vector store collection (document count, chunks, languages, etc.)",
        mimeType: "text/markdown",
      },
      {
        uri: "collection://documents",
        name: "Indexed Documents",
        description: "List all documents indexed in the vector store",
        mimeType: "text/markdown",
      },
      {
        uri: "collection://config",
        name: "Configuration",
        description:
          "View current Semche configuration (embedding model, chunk size, etc.)",
        mimeType: "text/markdown",
      },
    ],
  };
});

/**
 * リソース読み取りのハンドラー
 */
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  logger.info(`Reading resource: ${uri}`);

  try {
    let content: string;

    switch (uri) {
      case "collection://stats":
        content = await getStatsResource();
        break;

      case "collection://documents":
        content = await getDocumentsResource();
        break;

      case "collection://config":
        content = await getConfigResource();
        break;

      default:
        throw new Error(`Unknown resource: ${uri}`);
    }

    return {
      contents: [
        {
          uri,
          mimeType: "text/markdown",
          text: content,
        },
      ],
    };
  } catch (error) {
    logger.error(`Failed to read resource: ${uri}`, error);
    throw error;
  }
});
```

### 3. テストの作成

```typescript
// tests/resources/resources.test.ts
import {
  getStatsResource,
  getDocumentsResource,
  getConfigResource,
} from "../../src/resources/index";
import { indexDocuments } from "../../src/tools/indexDocuments";
import { getVectorStore, closeVectorStore } from "../../src/utils/vectorStore";

describe("MCP Resources", () => {
  beforeAll(async () => {
    // テストデータのインデックス
    await indexDocuments({
      documents: [
        {
          id: "resource-test-1",
          content: "Test document for resources",
          metadata: {
            filePath: "/test/resource.ts",
            language: "typescript",
          },
        },
      ],
      upsert: true,
    });
  });

  afterAll(async () => {
    await closeVectorStore();
  });

  describe("collection://stats", () => {
    test("should return stats in markdown format", async () => {
      const content = await getStatsResource();

      expect(content).toContain("# Semche Vector Store Statistics");
      expect(content).toContain("## Overview");
      expect(content).toContain("Documents:");
      expect(content).toContain("Chunks:");
    });

    test("should include language distribution", async () => {
      const content = await getStatsResource();

      expect(content).toContain("## Language Distribution");
      expect(content).toContain("typescript");
    });

    test("should include top files", async () => {
      const content = await getStatsResource();

      expect(content).toContain("## Top Files by Chunks");
    });
  });

  describe("collection://documents", () => {
    test("should return documents list in markdown format", async () => {
      const content = await getDocumentsResource();

      expect(content).toContain("# Indexed Documents");
      expect(content).toContain("Total files:");
      expect(content).toContain("/test/resource.ts");
    });

    test("should show chunk counts", async () => {
      const content = await getDocumentsResource();

      expect(content).toContain("Chunks:");
    });
  });

  describe("collection://config", () => {
    test("should return config in markdown format", async () => {
      const content = await getConfigResource();

      expect(content).toContain("# Semche Configuration");
      expect(content).toContain("## Vector Store Settings");
      expect(content).toContain("Collection Name:");
    });

    test("should include embedding model info", async () => {
      const content = await getConfigResource();

      expect(content).toContain("Embedding Model:");
      expect(content).toContain("sentence-transformers");
    });

    test("should include HNSW settings", async () => {
      const content = await getConfigResource();

      expect(content).toContain("## HNSW Index Settings");
      expect(content).toContain("Space:");
      expect(content).toContain("Construction EF:");
    });

    test("should include chunk settings", async () => {
      const content = await getConfigResource();

      expect(content).toContain("## Text Processing");
      expect(content).toContain("Chunk Size:");
      expect(content).toContain("Chunk Overlap:");
    });
  });
});
```

### 4. Cursor IDEでの使用例

Cursorチャットで以下のようにリソースを参照:

```
@collection://stats を見せて
```

```
@collection://documents に何がインデックスされてる?
```

```
@collection://config の設定を確認
```

## 完了条件

- [ ] src/resources/index.tsが実装されている
- [ ] MCPサーバーにリソースが統合されている
- [ ] 3つのリソース（stats, documents, config）が全て機能する
- [ ] リソースがMarkdown形式で返される
- [ ] ListResourcesRequestが正しく応答する
- [ ] ReadResourceRequestが正しく応答する
- [ ] テストが全てパスする
- [ ] Cursor IDEからリソースを参照できる
- [ ] .exp.mdドキュメントが更新されている

## 動作確認

### ローカルテスト

```bash
npm run test -- tests/resources/resources.test.ts
```

### Cursor IDEでの確認

1. サーバーを起動: `npm run dev`
2. Cursor IDEを再起動
3. チャットで「利用可能なリソースは？」と質問
4. 3つのリソースが表示されることを確認
5. `@collection://stats` のように参照して内容を確認

## リソースの使い道

### collection://stats

- コレクションの全体像を把握
- インデックスされたデータの統計
- 言語分布の確認

### collection://documents

- どのファイルがインデックスされているかを確認
- 重複インデックスのチェック
- ドキュメント一覧の取得

### collection://config

- 現在の設定の確認
- デバッグ時の設定確認
- パフォーマンスチューニングの参考

## トラブルシューティング

- リソースが表示されない: ListResourcesRequestハンドラーを確認
- 内容が空: ドキュメントがインデックスされているか確認
- エラーが出る: ログを確認してハンドラーの実装を見直す

## 次のタスク

タスク10: MCPプロンプトの実装
