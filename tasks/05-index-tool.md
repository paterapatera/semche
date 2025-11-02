# タスク5: indexDocumentsツールの実装

## 目的

ドキュメントをベクトルストアにインデックス化（追加・更新）する機能を実装する

## 作業内容

### 1. indexDocumentsツールハンドラーの作成

```typescript
// src/tools/indexDocuments.ts
import { getVectorStore } from "../utils/vectorStore.js";
import { splitText, splitCode } from "../utils/textSplitter.js";
import { logger } from "../utils/logger.js";
import { Document } from "@langchain/core/documents";
import crypto from "crypto";

export interface IndexDocumentInput {
  content: string;
  metadata?: {
    filePath?: string;
    language?: string;
    projectName?: string;
    [key: string]: any;
  };
  id?: string;
}

export interface IndexDocumentsOptions {
  documents: IndexDocumentInput[];
  upsert?: boolean;
}

/**
 * ドキュメントIDを生成
 */
function generateDocumentId(
  content: string,
  metadata?: Record<string, any>
): string {
  const idBase = metadata?.filePath
    ? `${metadata.filePath}::${content.substring(0, 100)}`
    : content.substring(0, 100);

  return crypto.createHash("sha256").update(idBase).digest("hex");
}

/**
 * indexDocumentsツールの実装
 */
export async function indexDocuments(options: IndexDocumentsOptions): Promise<{
  success: boolean;
  indexed: number;
  updated: number;
  chunks: number;
  message: string;
}> {
  const { documents, upsert = true } = options;

  logger.info(`Indexing ${documents.length} document(s), upsert: ${upsert}`);

  try {
    const vectorStore = await getVectorStore();

    let totalIndexed = 0;
    let totalUpdated = 0;
    let totalChunks = 0;

    for (const doc of documents) {
      // ドキュメントIDの生成または使用
      const docId = doc.id || generateDocumentId(doc.content, doc.metadata);

      // テキストをチャンクに分割
      let chunks: string[];
      if (doc.metadata?.language) {
        chunks = await splitCode(doc.content, doc.metadata.language);
      } else {
        chunks = await splitText(doc.content);
      }

      logger.info(`Document ${docId}: ${chunks.length} chunks created`);

      // upsert処理: 既存ドキュメントの削除
      if (upsert) {
        try {
          // 同じIDのドキュメントを削除
          await vectorStore.delete({ ids: [docId] });
          logger.info(`Deleted existing document: ${docId}`);
          totalUpdated++;
        } catch (error) {
          // ドキュメントが存在しない場合のエラーは無視
          logger.debug(`No existing document to delete: ${docId}`);
          totalIndexed++;
        }
      } else {
        totalIndexed++;
      }

      // チャンクごとにDocumentオブジェクトを作成
      const langchainDocs = chunks.map((chunk, index) => {
        return new Document({
          pageContent: chunk,
          metadata: {
            ...doc.metadata,
            documentId: docId,
            chunkIndex: index,
            totalChunks: chunks.length,
            indexedAt: new Date().toISOString(),
          },
        });
      });

      // ベクトルストアに追加
      await vectorStore.addDocuments(langchainDocs);

      totalChunks += chunks.length;

      logger.info(`Indexed document ${docId}: ${chunks.length} chunks`);
    }

    const message = upsert
      ? `Successfully indexed ${totalIndexed} new and updated ${totalUpdated} existing documents (${totalChunks} chunks total)`
      : `Successfully indexed ${totalIndexed} documents (${totalChunks} chunks total)`;

    return {
      success: true,
      indexed: totalIndexed,
      updated: totalUpdated,
      chunks: totalChunks,
      message,
    };
  } catch (error) {
    logger.error("Failed to index documents", error);
    throw error;
  }
}
```

### 2. MCPサーバーへのツール統合

```typescript
// src/index.ts (CallToolRequestSchema ハンドラーを更新)
import { indexDocuments } from "./tools/indexDocuments.js";

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
// tests/tools/indexDocuments.test.ts
import { indexDocuments } from "../../src/tools/indexDocuments";
import { getVectorStore, closeVectorStore } from "../../src/utils/vectorStore";

describe("indexDocuments", () => {
  afterAll(async () => {
    await closeVectorStore();
  });

  test("should index a single document", async () => {
    const result = await indexDocuments({
      documents: [
        {
          content: "This is a test document for vector search.",
          metadata: {
            filePath: "/test/example.txt",
            language: "text",
          },
        },
      ],
      upsert: false,
    });

    expect(result.success).toBe(true);
    expect(result.indexed).toBe(1);
    expect(result.chunks).toBeGreaterThan(0);
  });

  test("should index multiple documents", async () => {
    const result = await indexDocuments({
      documents: [
        {
          content: "First document content",
          metadata: { filePath: "/test/doc1.txt" },
        },
        {
          content: "Second document content",
          metadata: { filePath: "/test/doc2.txt" },
        },
      ],
    });

    expect(result.success).toBe(true);
    expect(result.indexed).toBeGreaterThanOrEqual(1);
  });

  test("should upsert existing document", async () => {
    const docData = {
      documents: [
        {
          id: "test-doc-upsert",
          content: "Original content",
          metadata: { filePath: "/test/upsert.txt" },
        },
      ],
      upsert: true,
    };

    // 最初のインデックス
    const result1 = await indexDocuments(docData);
    expect(result1.indexed).toBe(1);
    expect(result1.updated).toBe(0);

    // 同じIDで再度インデックス（upsert）
    const result2 = await indexDocuments({
      documents: [
        {
          id: "test-doc-upsert",
          content: "Updated content",
          metadata: { filePath: "/test/upsert.txt" },
        },
      ],
      upsert: true,
    });

    expect(result2.updated).toBe(1);
  });

  test("should handle code splitting", async () => {
    const codeContent = `
function add(a: number, b: number): number {
  return a + b;
}

function multiply(a: number, b: number): number {
  return a * b;
}

class Calculator {
  calculate(operation: string, a: number, b: number): number {
    if (operation === 'add') return add(a, b);
    if (operation === 'multiply') return multiply(a, b);
    throw new Error('Unknown operation');
  }
}
    `.trim();

    const result = await indexDocuments({
      documents: [
        {
          content: codeContent,
          metadata: {
            filePath: "/test/calculator.ts",
            language: "typescript",
          },
        },
      ],
    });

    expect(result.success).toBe(true);
    expect(result.chunks).toBeGreaterThan(0);
  });
});
```

### 4. Cursor IDEでの使用例

Cursorチャットで以下のように使用:

```
このファイルをベクトルストアにインデックスしてください
```

または:

```
src/utils/logger.tsの内容をsemcheにインデックス
```

MCPツールとして直接呼び出す場合:

```json
{
  "tool": "indexDocuments",
  "arguments": {
    "documents": [
      {
        "content": "export function add(a: number, b: number) { return a + b; }",
        "metadata": {
          "filePath": "/src/math.ts",
          "language": "typescript",
          "projectName": "my-project"
        }
      }
    ],
    "upsert": true
  }
}
```

## 完了条件

- [ ] src/tools/indexDocuments.tsが実装されている
- [ ] MCPサーバーにツールが統合されている
- [ ] ドキュメントIDの生成が正しく機能する
- [ ] upsert処理が正しく動作する（既存ドキュメントを更新）
- [ ] テキストとコードの分割が正しく機能する
- [ ] テストが全てパスする
- [ ] Cursor IDEからツールを呼び出せる

## 動作確認

### ローカルテスト

```bash
npm run test -- tests/tools/indexDocuments.test.ts
```

### Cursor IDEでの確認

1. サーバーを再起動: `npm run dev`
2. Cursor IDEを再起動
3. チャットで「このファイルをインデックス」と指示
4. 成功メッセージとインデックスされたチャンク数を確認

## トラブルシューティング

- チャンク数が0: テキストが短すぎる可能性（最小長を確認）
- upsertが機能しない: ドキュメントID生成ロジックを確認
- メモリエラー: チャンクサイズを調整（CHUNK_SIZE環境変数）

## 次のタスク

タスク6: searchツールの実装
