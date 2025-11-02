# タスク6: searchツールの実装

## 目的

セマンティック検索機能を実装し、Cursor IDEから自然言語でコードやドキュメントを検索可能にする

## 作業内容

### 1. searchツールハンドラーの作成

````typescript
// src/tools/search.ts
import { getVectorStore } from "../utils/vectorStore.js";
import { logger } from "../utils/logger.js";
import { Document } from "@langchain/core/documents";

export interface SearchOptions {
  query: string;
  k?: number;
  filter?: Record<string, any>;
  scoreThreshold?: number;
}

export interface SearchResult {
  content: string;
  metadata: Record<string, any>;
  score: number;
}

/**
 * searchツールの実装
 */
export async function search(options: SearchOptions): Promise<{
  success: boolean;
  results: SearchResult[];
  query: string;
  resultCount: number;
  message: string;
}> {
  const { query, k = 5, filter, scoreThreshold = 0.0 } = options;

  logger.info(
    `Searching for: "${query}" (k=${k}, threshold=${scoreThreshold})`
  );

  if (filter) {
    logger.info("Filter applied", filter);
  }

  try {
    const vectorStore = await getVectorStore();

    // 類似度検索（スコア付き）
    const results = await vectorStore.similaritySearchWithScore(
      query,
      k,
      filter
    );

    // スコア閾値でフィルタリング
    const filteredResults = results.filter(
      ([_, score]) => score >= scoreThreshold
    );

    // 結果を整形
    const formattedResults: SearchResult[] = filteredResults.map(
      ([doc, score]) => ({
        content: doc.pageContent,
        metadata: doc.metadata,
        score: Math.round((1 - score) * 100) / 100, // 類似度に変換（0-1）
      })
    );

    logger.info(
      `Found ${formattedResults.length} results (filtered from ${results.length})`
    );

    // 結果をスコア順にソート（降順）
    formattedResults.sort((a, b) => b.score - a.score);

    return {
      success: true,
      results: formattedResults,
      query,
      resultCount: formattedResults.length,
      message: `Found ${formattedResults.length} relevant document(s)`,
    };
  } catch (error) {
    logger.error("Search failed", error);
    throw error;
  }
}

/**
 * 検索結果を人間が読みやすいテキストに変換
 */
export function formatSearchResults(
  results: SearchResult[],
  options: { includeMetadata?: boolean; maxContentLength?: number } = {}
): string {
  const { includeMetadata = true, maxContentLength = 500 } = options;

  if (results.length === 0) {
    return "No results found.";
  }

  return results
    .map((result, index) => {
      let output = `## Result ${index + 1} (Score: ${result.score})\n\n`;

      // コンテンツ（必要に応じて切り詰め）
      const content =
        result.content.length > maxContentLength
          ? result.content.substring(0, maxContentLength) + "..."
          : result.content;

      output += "```\n" + content + "\n```\n";

      // メタデータ
      if (includeMetadata && Object.keys(result.metadata).length > 0) {
        output += "\n**Metadata:**\n";
        output += "- File: " + (result.metadata.filePath || "N/A") + "\n";
        output += "- Language: " + (result.metadata.language || "N/A") + "\n";
        output +=
          "- Chunk: " +
          (result.metadata.chunkIndex !== undefined
            ? `${result.metadata.chunkIndex + 1}/${result.metadata.totalChunks}`
            : "N/A") +
          "\n";
        output += "- Indexed: " + (result.metadata.indexedAt || "N/A") + "\n";
      }

      return output;
    })
    .join("\n\n---\n\n");
}
````

### 2. MCPサーバーへのツール統合

```typescript
// src/index.ts (CallToolRequestSchema ハンドラーを更新)
import { search, formatSearchResults } from "./tools/search.js";

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

        // 人間が読みやすい形式で返す
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
// tests/tools/search.test.ts
import { search } from "../../src/tools/search";
import { indexDocuments } from "../../src/tools/indexDocuments";
import { getVectorStore, closeVectorStore } from "../../src/utils/vectorStore";

describe("search", () => {
  beforeAll(async () => {
    // テストデータのインデックス
    await indexDocuments({
      documents: [
        {
          id: "test-doc-1",
          content: "This is a function that calculates the sum of two numbers.",
          metadata: {
            filePath: "/test/math.ts",
            language: "typescript",
          },
        },
        {
          id: "test-doc-2",
          content:
            "This is a class that represents a user with name and email.",
          metadata: {
            filePath: "/test/user.ts",
            language: "typescript",
          },
        },
        {
          id: "test-doc-3",
          content: "Database connection configuration for PostgreSQL.",
          metadata: {
            filePath: "/test/database.ts",
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

  test("should find relevant documents", async () => {
    const result = await search({
      query: "how to add two numbers",
      k: 3,
    });

    expect(result.success).toBe(true);
    expect(result.results.length).toBeGreaterThan(0);
    expect(result.results[0].content).toContain("sum");
  });

  test("should respect k parameter", async () => {
    const result = await search({
      query: "typescript code",
      k: 2,
    });

    expect(result.results.length).toBeLessThanOrEqual(2);
  });

  test("should filter by metadata", async () => {
    const result = await search({
      query: "code",
      k: 5,
      filter: { filePath: "/test/user.ts" },
    });

    expect(result.success).toBe(true);
    expect(
      result.results.every((r) => r.metadata.filePath === "/test/user.ts")
    ).toBe(true);
  });

  test("should apply score threshold", async () => {
    const result = await search({
      query: "irrelevant query xyz",
      k: 10,
      scoreThreshold: 0.5,
    });

    // 低スコアの結果は除外される
    expect(result.results.every((r) => r.score >= 0.5)).toBe(true);
  });

  test("should return empty results for no match", async () => {
    const result = await search({
      query: "completely unrelated xyzabc123",
      k: 5,
      scoreThreshold: 0.9,
    });

    expect(result.success).toBe(true);
    expect(result.results.length).toBe(0);
  });
});
```

### 4. Cursor IDEでの使用例

```
ユーザー認証に関するコードを探して
```

```
データベース接続の設定を見つけて
```

```
TypeScriptで書かれた関数を検索
```

MCPツールとして直接呼び出す場合:

```json
{
  "tool": "search",
  "arguments": {
    "query": "function to calculate total price",
    "k": 5,
    "filter": {
      "language": "typescript"
    }
  }
}
```

## 完了条件

- [ ] src/tools/search.tsが実装されている
- [ ] MCPサーバーにツールが統合されている
- [ ] 類似度検索が正しく機能する
- [ ] メタデータフィルターが機能する
- [ ] スコア閾値フィルタリングが機能する
- [ ] 結果の整形が適切に行われる
- [ ] テストが全てパスする
- [ ] Cursor IDEから検索が実行できる

## 動作確認

### ローカルテスト

```bash
npm run test -- tests/tools/search.test.ts
```

### Cursor IDEでの確認

1. いくつかのファイルをインデックス:

   ```
   このプロジェクトの全ファイルをインデックスして
   ```

2. 検索を実行:

   ```
   ユーザー認証のコードを探して
   ```

3. 結果を確認（関連するコードスニペットが表示される）

## 検索クエリの例

### コード検索

- "エラーハンドリングの実装"
- "APIリクエストを送信する関数"
- "データベースからユーザーを取得"

### セマンティック検索

- "どうやって認証するの？"
- "ファイルをアップロードする方法"
- "レート制限の実装"

## トラブルシューティング

- 結果が返らない: インデックスされたドキュメントがあるか確認
- スコアが低い: 埋め込みモデルが適切か確認（多言語対応モデル使用）
- メタデータフィルターが効かない: フィールド名とデータ型を確認

## 次のタスク

タスク7: deleteDocumentsツールの実装
