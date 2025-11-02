# タスク7: deleteDocumentsツールの実装

## 目的

ベクトルストアからドキュメントを削除する機能を実装する

## 作業内容

### 1. deleteDocumentsツールハンドラーの作成

```typescript
// src/tools/deleteDocuments.ts
import { getVectorStore } from "../utils/vectorStore.js";
import { logger } from "../utils/logger.js";

export interface DeleteDocumentsOptions {
  ids?: string[];
  filter?: Record<string, any>;
}

/**
 * deleteDocumentsツールの実装
 */
export async function deleteDocuments(
  options: DeleteDocumentsOptions
): Promise<{
  success: boolean;
  deleted: number;
  message: string;
}> {
  const { ids, filter } = options;

  // idsもfilterも指定されていない場合はエラー
  if (!ids && !filter) {
    throw new Error("Either 'ids' or 'filter' must be provided for deletion");
  }

  logger.info("Deleting documents", { ids, filter });

  try {
    const vectorStore = await getVectorStore();

    let deletedCount = 0;

    // IDによる削除
    if (ids && ids.length > 0) {
      await vectorStore.delete({ ids });
      deletedCount = ids.length;
      logger.info(`Deleted ${deletedCount} documents by ID`);
    }

    // フィルターによる削除
    if (filter) {
      // フィルターに一致するドキュメントを検索
      const results = await vectorStore.similaritySearch("", 1000, filter);

      if (results.length > 0) {
        // 各ドキュメントのIDを抽出
        const idsToDelete = results
          .map((doc) => doc.metadata.documentId)
          .filter((id): id is string => !!id);

        // 重複を削除
        const uniqueIds = Array.from(new Set(idsToDelete));

        if (uniqueIds.length > 0) {
          await vectorStore.delete({ ids: uniqueIds });
          deletedCount += uniqueIds.length;
          logger.info(`Deleted ${uniqueIds.length} documents by filter`);
        }
      } else {
        logger.info("No documents found matching filter");
      }
    }

    return {
      success: true,
      deleted: deletedCount,
      message: `Successfully deleted ${deletedCount} document(s)`,
    };
  } catch (error) {
    logger.error("Failed to delete documents", error);
    throw error;
  }
}

/**
 * 特定のファイルパスに関連するドキュメントを削除
 */
export async function deleteDocumentsByFilePath(filePath: string): Promise<{
  success: boolean;
  deleted: number;
  message: string;
}> {
  return deleteDocuments({
    filter: { filePath },
  });
}

/**
 * 特定のプロジェクトに関連するドキュメントを削除
 */
export async function deleteDocumentsByProject(projectName: string): Promise<{
  success: boolean;
  deleted: number;
  message: string;
}> {
  return deleteDocuments({
    filter: { projectName },
  });
}

/**
 * 全てのドキュメントを削除（危険な操作）
 */
export async function deleteAllDocuments(): Promise<{
  success: boolean;
  deleted: number;
  message: string;
}> {
  logger.warn("DELETING ALL DOCUMENTS - This cannot be undone!");

  try {
    const vectorStore = await getVectorStore();

    // 全ドキュメントを検索
    const allDocs = await vectorStore.similaritySearch("", 10000);

    if (allDocs.length === 0) {
      return {
        success: true,
        deleted: 0,
        message: "No documents to delete",
      };
    }

    const idsToDelete = allDocs
      .map((doc) => doc.metadata.documentId)
      .filter((id): id is string => !!id);

    const uniqueIds = Array.from(new Set(idsToDelete));

    await vectorStore.delete({ ids: uniqueIds });

    logger.info(`Deleted all documents: ${uniqueIds.length}`);

    return {
      success: true,
      deleted: uniqueIds.length,
      message: `Successfully deleted all ${uniqueIds.length} document(s)`,
    };
  } catch (error) {
    logger.error("Failed to delete all documents", error);
    throw error;
  }
}
```

### 2. MCPサーバーへのツール統合

```typescript
// src/index.ts (CallToolRequestSchema ハンドラーを更新)
import { deleteDocuments } from "./tools/deleteDocuments.js";

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
// tests/tools/deleteDocuments.test.ts
import {
  deleteDocuments,
  deleteDocumentsByFilePath,
} from "../../src/tools/deleteDocuments";
import { indexDocuments } from "../../src/tools/indexDocuments";
import { search } from "../../src/tools/search";
import { getVectorStore, closeVectorStore } from "../../src/utils/vectorStore";

describe("deleteDocuments", () => {
  beforeEach(async () => {
    // テストデータのインデックス
    await indexDocuments({
      documents: [
        {
          id: "delete-test-1",
          content: "Document 1 content",
          metadata: { filePath: "/test/file1.ts" },
        },
        {
          id: "delete-test-2",
          content: "Document 2 content",
          metadata: { filePath: "/test/file2.ts" },
        },
        {
          id: "delete-test-3",
          content: "Document 3 content",
          metadata: { filePath: "/test/file3.ts" },
        },
      ],
      upsert: true,
    });
  });

  afterAll(async () => {
    await closeVectorStore();
  });

  test("should delete documents by IDs", async () => {
    const result = await deleteDocuments({
      ids: ["delete-test-1", "delete-test-2"],
    });

    expect(result.success).toBe(true);
    expect(result.deleted).toBe(2);

    // 削除を確認
    const searchResult = await search({ query: "Document 1", k: 5 });
    const foundDoc1 = searchResult.results.some((r) =>
      r.content.includes("Document 1")
    );
    expect(foundDoc1).toBe(false);
  });

  test("should delete documents by filter", async () => {
    const result = await deleteDocuments({
      filter: { filePath: "/test/file1.ts" },
    });

    expect(result.success).toBe(true);
    expect(result.deleted).toBeGreaterThan(0);

    // 削除を確認
    const searchResult = await search({
      query: "content",
      k: 10,
      filter: { filePath: "/test/file1.ts" },
    });
    expect(searchResult.results.length).toBe(0);
  });

  test("should delete documents by filePath helper", async () => {
    const result = await deleteDocumentsByFilePath("/test/file2.ts");

    expect(result.success).toBe(true);
    expect(result.deleted).toBeGreaterThan(0);
  });

  test("should throw error if no ids or filter provided", async () => {
    await expect(deleteDocuments({})).rejects.toThrow(
      "Either 'ids' or 'filter' must be provided"
    );
  });

  test("should handle non-existent IDs gracefully", async () => {
    const result = await deleteDocuments({
      ids: ["non-existent-id-xyz"],
    });

    // エラーではなく、削除数0で成功
    expect(result.success).toBe(true);
  });
});
```

### 4. Cursor IDEでの使用例

```
このファイルをベクトルストアから削除して
```

```
/src/old-code.tsのインデックスを削除
```

```
プロジェクト "legacy-app" のドキュメントを全て削除
```

MCPツールとして直接呼び出す場合:

```json
{
  "tool": "deleteDocuments",
  "arguments": {
    "filter": {
      "filePath": "/src/deprecated/old-module.ts"
    }
  }
}
```

または IDで削除:

```json
{
  "tool": "deleteDocuments",
  "arguments": {
    "ids": ["doc-id-1", "doc-id-2"]
  }
}
```

## 完了条件

- [ ] src/tools/deleteDocuments.tsが実装されている
- [ ] MCPサーバーにツールが統合されている
- [ ] IDによる削除が機能する
- [ ] フィルターによる削除が機能する
- [ ] ヘルパー関数（ファイルパス、プロジェクト）が機能する
- [ ] エラーハンドリングが適切
- [ ] テストが全てパスする
- [ ] Cursor IDEから削除が実行できる
- [ ] .exp.mdドキュメントが更新されている

## 動作確認

### ローカルテスト

```bash
npm run test -- tests/tools/deleteDocuments.test.ts
```

### Cursor IDEでの確認

1. ドキュメントをインデックス:

   ```
   このファイルをインデックス
   ```

2. 検索で存在を確認:

   ```
   このファイルの内容を検索
   ```

3. 削除を実行:

   ```
   このファイルのインデックスを削除
   ```

4. 再度検索して削除を確認:
   ```
   このファイルの内容を検索
   ```
   → "No results found" となるはず

## 安全性の考慮

- 削除は元に戻せないため、確認なしでは実行しない
- 全削除機能（deleteAllDocuments）は特に慎重に使用
- 本番環境では削除前にバックアップを推奨

## トラブルシューティング

- 削除されない: documentIdメタデータが正しく設定されているか確認
- フィルターで削除できない: メタデータのフィールド名を確認
- 一部のみ削除される: チャンクごとにdocumentIdが設定されているか確認

## 次のタスク

タスク8: getCollectionInfoツールの実装
