# タスク8: getCollectionInfoツールの実装

## 目的

ベクトルストアのコレクション情報を取得し、インデックスの統計情報を提供する

## 作業内容

### 1. getCollectionInfoツールハンドラーの作成

```typescript
// src/tools/getCollectionInfo.ts
import { getVectorStore } from "../utils/vectorStore.js";
import { logger } from "../utils/logger.js";
import { config } from "../config.js";

export interface CollectionInfo {
  collectionName: string;
  documentCount: number;
  chunkCount: number;
  uniqueFiles: number;
  languages: string[];
  embeddingModel: string;
  embeddingDimension: number;
  persistDirectory: string;
  storageSize?: string;
  recentDocuments: Array<{
    documentId: string;
    filePath: string;
    indexedAt: string;
  }>;
}

/**
 * getCollectionInfoツールの実装
 */
export async function getCollectionInfo(): Promise<{
  success: boolean;
  info: CollectionInfo;
  message: string;
}> {
  logger.info("Getting collection info");

  try {
    const vectorStore = await getVectorStore();

    // 全ドキュメントを取得して統計を計算
    // 注: 大規模なコレクションでは最適化が必要
    const allChunks = await vectorStore.similaritySearch("", 10000);

    // ユニークなドキュメントID
    const documentIds = new Set(
      allChunks
        .map((doc) => doc.metadata.documentId)
        .filter((id): id is string => !!id)
    );

    // ユニークなファイルパス
    const filePaths = new Set(
      allChunks
        .map((doc) => doc.metadata.filePath)
        .filter((path): path is string => !!path)
    );

    // 言語の集計
    const languages = Array.from(
      new Set(
        allChunks
          .map((doc) => doc.metadata.language)
          .filter((lang): lang is string => !!lang)
      )
    );

    // 最近インデックスされたドキュメント（上位5件）
    const recentDocs = allChunks
      .filter((doc) => doc.metadata.indexedAt)
      .sort(
        (a, b) =>
          new Date(b.metadata.indexedAt).getTime() -
          new Date(a.metadata.indexedAt).getTime()
      )
      .slice(0, 5)
      .map((doc) => ({
        documentId: doc.metadata.documentId || "unknown",
        filePath: doc.metadata.filePath || "unknown",
        indexedAt: doc.metadata.indexedAt,
      }));

    // ストレージサイズの取得（オプション）
    let storageSize: string | undefined;
    try {
      const fs = await import("fs");
      const path = await import("path");
      const stats = fs.statSync(
        path.join(config.persistDirectory, "chroma.sqlite3")
      );
      const sizeInMB = (stats.size / (1024 * 1024)).toFixed(2);
      storageSize = `${sizeInMB} MB`;
    } catch (error) {
      logger.debug("Could not determine storage size", error);
    }

    const info: CollectionInfo = {
      collectionName: config.collectionName,
      documentCount: documentIds.size,
      chunkCount: allChunks.length,
      uniqueFiles: filePaths.size,
      languages: languages.length > 0 ? languages : ["unknown"],
      embeddingModel: config.embeddingModel,
      embeddingDimension: config.embeddingDimension,
      persistDirectory: config.persistDirectory,
      storageSize,
      recentDocuments: recentDocs,
    };

    logger.info("Collection info retrieved", info);

    return {
      success: true,
      info,
      message: "Collection information retrieved successfully",
    };
  } catch (error) {
    logger.error("Failed to get collection info", error);
    throw error;
  }
}

/**
 * コレクション情報を人間が読みやすいテキストに変換
 */
export function formatCollectionInfo(info: CollectionInfo): string {
  let output = "# Vector Store Collection Info\n\n";

  output += `**Collection Name:** ${info.collectionName}\n`;
  output += `**Documents:** ${info.documentCount}\n`;
  output += `**Chunks:** ${info.chunkCount}\n`;
  output += `**Files:** ${info.uniqueFiles}\n`;
  output += `**Languages:** ${info.languages.join(", ")}\n`;
  output += `**Embedding Model:** ${info.embeddingModel}\n`;
  output += `**Embedding Dimension:** ${info.embeddingDimension}\n`;
  output += `**Storage:** ${info.persistDirectory}\n`;

  if (info.storageSize) {
    output += `**Storage Size:** ${info.storageSize}\n`;
  }

  if (info.recentDocuments.length > 0) {
    output += "\n## Recent Documents\n\n";
    info.recentDocuments.forEach((doc, index) => {
      output += `${index + 1}. **${doc.filePath}**\n`;
      output += `   - ID: ${doc.documentId}\n`;
      output += `   - Indexed: ${doc.indexedAt}\n\n`;
    });
  }

  return output;
}

/**
 * 言語別のドキュメント数を取得
 */
export async function getLanguageStats(): Promise<Record<string, number>> {
  const vectorStore = await getVectorStore();
  const allChunks = await vectorStore.similaritySearch("", 10000);

  const stats: Record<string, number> = {};

  allChunks.forEach((doc) => {
    const lang = doc.metadata.language || "unknown";
    stats[lang] = (stats[lang] || 0) + 1;
  });

  return stats;
}

/**
 * ファイル別のチャンク数を取得
 */
export async function getFileStats(): Promise<
  Array<{ filePath: string; chunks: number }>
> {
  const vectorStore = await getVectorStore();
  const allChunks = await vectorStore.similaritySearch("", 10000);

  const stats: Record<string, number> = {};

  allChunks.forEach((doc) => {
    const filePath = doc.metadata.filePath || "unknown";
    stats[filePath] = (stats[filePath] || 0) + 1;
  });

  return Object.entries(stats)
    .map(([filePath, chunks]) => ({ filePath, chunks }))
    .sort((a, b) => b.chunks - a.chunks);
}
```

### 2. MCPサーバーへのツール統合

```typescript
// src/index.ts (CallToolRequestSchema ハンドラーを更新)
import {
  getCollectionInfo,
  formatCollectionInfo,
} from "./tools/getCollectionInfo.js";

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  logger.info(`Tool called: ${name}`, args);

  try {
    switch (name) {
      case "indexDocuments": {
        const result = await indexDocuments(args as any);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "search": {
        const result = await search(args as any);
        const formattedText = formatSearchResults(result.results, {
          includeMetadata: true,
          maxContentLength: 500,
        });

        return {
          content: [
            {
              type: "text",
              text: `# Search Results\n\nQuery: "${result.query}"\nFound: ${result.resultCount} result(s)\n\n${formattedText}`,
            },
          ],
        };
      }

      case "deleteDocuments": {
        const result = await deleteDocuments(args as any);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "getCollectionInfo": {
        const result = await getCollectionInfo();
        const formattedText = formatCollectionInfo(result.info);

        return {
          content: [
            {
              type: "text",
              text: formattedText,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    logger.error(`Tool execution failed: ${name}`, error);

    return {
      content: [
        {
          type: "text",
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});
```

### 3. テストの作成

```typescript
// tests/tools/getCollectionInfo.test.ts
import {
  getCollectionInfo,
  getLanguageStats,
  getFileStats,
} from "../../src/tools/getCollectionInfo";
import { indexDocuments } from "../../src/tools/indexDocuments";
import { getVectorStore, closeVectorStore } from "../../src/utils/vectorStore";

describe("getCollectionInfo", () => {
  beforeAll(async () => {
    // テストデータのインデックス
    await indexDocuments({
      documents: [
        {
          id: "info-test-1",
          content: "TypeScript code example",
          metadata: { filePath: "/test/example.ts", language: "typescript" },
        },
        {
          id: "info-test-2",
          content: "Python code example",
          metadata: { filePath: "/test/example.py", language: "python" },
        },
        {
          id: "info-test-3",
          content: "More TypeScript code",
          metadata: { filePath: "/test/utils.ts", language: "typescript" },
        },
      ],
      upsert: true,
    });
  });

  afterAll(async () => {
    await closeVectorStore();
  });

  test("should retrieve collection info", async () => {
    const result = await getCollectionInfo();

    expect(result.success).toBe(true);
    expect(result.info.collectionName).toBeDefined();
    expect(result.info.documentCount).toBeGreaterThan(0);
    expect(result.info.chunkCount).toBeGreaterThan(0);
    expect(result.info.uniqueFiles).toBeGreaterThan(0);
  });

  test("should track multiple languages", async () => {
    const result = await getCollectionInfo();

    expect(result.info.languages).toContain("typescript");
    expect(result.info.languages).toContain("python");
  });

  test("should list recent documents", async () => {
    const result = await getCollectionInfo();

    expect(result.info.recentDocuments.length).toBeGreaterThan(0);
    expect(result.info.recentDocuments[0].filePath).toBeDefined();
    expect(result.info.recentDocuments[0].indexedAt).toBeDefined();
  });

  test("should get language statistics", async () => {
    const stats = await getLanguageStats();

    expect(stats.typescript).toBeGreaterThan(0);
    expect(stats.python).toBeGreaterThan(0);
  });

  test("should get file statistics", async () => {
    const stats = await getFileStats();

    expect(stats.length).toBeGreaterThan(0);
    expect(stats[0].filePath).toBeDefined();
    expect(stats[0].chunks).toBeGreaterThan(0);
  });

  test("should include embedding model info", async () => {
    const result = await getCollectionInfo();

    expect(result.info.embeddingModel).toContain("sentence-transformers");
    expect(result.info.embeddingDimension).toBe(768);
  });
});
```

### 4. Cursor IDEでの使用例

```
ベクトルストアの状態を教えて
```

```
インデックスされているドキュメントの統計を見せて
```

```
どれくらいのファイルがインデックスされてる?
```

MCPツールとして直接呼び出す場合:

```json
{
  "tool": "getCollectionInfo",
  "arguments": {}
}
```

## 完了条件

- [ ] src/tools/getCollectionInfo.tsが実装されている
- [ ] MCPサーバーにツールが統合されている
- [ ] ドキュメント数、チャンク数が正確に表示される
- [ ] ユニークなファイル数が正しく計算される
- [ ] 言語の統計が正しく集計される
- [ ] 最近のドキュメントが表示される
- [ ] テストが全てパスする
- [ ] Cursor IDEから情報を取得できる

## 動作確認

### ローカルテスト

```bash
npm run test -- tests/tools/getCollectionInfo.test.ts
```

### Cursor IDEでの確認

1. いくつかのファイルをインデックス:

   ```
   プロジェクト全体をインデックス
   ```

2. コレクション情報を取得:

   ```
   ベクトルストアの統計情報を表示
   ```

3. 結果確認:
   - ドキュメント数
   - チャンク数
   - ファイル数
   - 使用言語
   - 最近インデックスされたファイル

## パフォーマンスの考慮

- 大規模コレクション（10,000+チャンク）では処理に時間がかかる可能性
- 将来的にはChromaDBのネイティブ統計APIを使用することを検討
- キャッシュ機能の追加を検討

## トラブルシューティング

- 統計が0になる: ドキュメントがインデックスされているか確認
- ストレージサイズが表示されない: chroma.sqlite3ファイルの存在を確認
- 言語が "unknown": メタデータにlanguageフィールドが設定されているか確認

## 次のタスク

タスク9: MCPリソースの実装
