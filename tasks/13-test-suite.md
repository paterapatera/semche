# タスク13: テストスイートの完成

## 目的

包括的なテストスイートを完成させ、コードの品質と信頼性を確保する

## 作業内容

### 1. Jest設定の最適化

```javascript
// jest.config.js
export default {
  preset: "ts-jest/presets/default-esm",
  testEnvironment: "node",
  extensionsToTreatAsEsm: [".ts"],
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        useESM: true,
      },
    ],
  },
  testMatch: ["**/tests/**/*.test.ts"],
  collectCoverageFrom: ["src/**/*.ts", "!src/**/*.d.ts", "!src/index.ts"],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov", "html"],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  setupFilesAfterEnv: ["<rootDir>/tests/setup.ts"],
  testTimeout: 30000, // 30秒（埋め込みモデルのロードに時間がかかる場合）
};
```

### 2. テストセットアップファイルの作成

```typescript
// tests/setup.ts
import { getVectorStore, closeVectorStore } from "../src/utils/vectorStore";
import { config } from "../src/config";

// テスト用の環境変数を設定
process.env.NODE_ENV = "test";
process.env.COLLECTION_NAME = "semche-test-collection";
process.env.PERSIST_DIRECTORY = "./data/test-chroma";
process.env.LOG_LEVEL = "error"; // テスト中はエラーのみ表示

// グローバルセットアップ
beforeAll(async () => {
  console.log("Setting up test environment...");
});

// グローバルクリーンアップ
afterAll(async () => {
  console.log("Cleaning up test environment...");
  await closeVectorStore();
});
```

### 3. 統合テストの作成

```typescript
// tests/integration/fullWorkflow.test.ts
import { indexDocuments } from "../../src/tools/indexDocuments";
import { search } from "../../src/tools/search";
import { deleteDocuments } from "../../src/tools/deleteDocuments";
import { getCollectionInfo } from "../../src/tools/getCollectionInfo";
import { getVectorStore, closeVectorStore } from "../../src/utils/vectorStore";

describe("Full Workflow Integration Test", () => {
  const testDocs = [
    {
      id: "integration-test-1",
      content: `
        export class UserService {
          async createUser(name: string, email: string) {
            return { id: 1, name, email };
          }
        }
      `,
      metadata: {
        filePath: "/test/services/userService.ts",
        language: "typescript",
      },
    },
    {
      id: "integration-test-2",
      content: `
        export class AuthService {
          async login(email: string, password: string) {
            return { token: "abc123" };
          }
        }
      `,
      metadata: {
        filePath: "/test/services/authService.ts",
        language: "typescript",
      },
    },
    {
      id: "integration-test-3",
      content: `
        export class DatabaseConnection {
          async connect(connectionString: string) {
            console.log("Connected to database");
          }
        }
      `,
      metadata: {
        filePath: "/test/database/connection.ts",
        language: "typescript",
      },
    },
  ];

  afterAll(async () => {
    // テストデータをクリーンアップ
    await deleteDocuments({
      ids: testDocs.map((d) => d.id),
    });
    await closeVectorStore();
  });

  test("Complete workflow: index -> search -> update -> delete", async () => {
    // 1. インデックス
    const indexResult = await indexDocuments({
      documents: testDocs,
      upsert: false,
    });

    expect(indexResult.success).toBe(true);
    expect(indexResult.indexed).toBe(3);

    // 2. 検索
    const searchResult = await search({
      query: "user authentication",
      k: 5,
    });

    expect(searchResult.success).toBe(true);
    expect(searchResult.results.length).toBeGreaterThan(0);

    // AuthServiceが最も関連性が高いはず
    const authServiceResult = searchResult.results.find((r) =>
      r.metadata.filePath?.includes("authService")
    );
    expect(authServiceResult).toBeDefined();

    // 3. コレクション情報の取得
    const infoResult = await getCollectionInfo();

    expect(infoResult.success).toBe(true);
    expect(infoResult.info.documentCount).toBeGreaterThanOrEqual(3);

    // 4. ドキュメントの更新（upsert）
    const updateResult = await indexDocuments({
      documents: [
        {
          id: "integration-test-1",
          content: `
            export class UserService {
              async createUser(name: string, email: string) {
                // Updated implementation
                return { id: 1, name, email, createdAt: new Date() };
              }
            }
          `,
          metadata: {
            filePath: "/test/services/userService.ts",
            language: "typescript",
          },
        },
      ],
      upsert: true,
    });

    expect(updateResult.success).toBe(true);
    expect(updateResult.updated).toBe(1);

    // 5. 更新された内容を検索
    const updatedSearchResult = await search({
      query: "createdAt",
      k: 5,
    });

    expect(updatedSearchResult.results.length).toBeGreaterThan(0);
    expect(updatedSearchResult.results[0].content).toContain("createdAt");

    // 6. 特定のドキュメントを削除
    const deleteResult = await deleteDocuments({
      ids: ["integration-test-3"],
    });

    expect(deleteResult.success).toBe(true);
    expect(deleteResult.deleted).toBe(1);

    // 7. 削除を確認
    const finalSearchResult = await search({
      query: "database connection",
      k: 5,
    });

    const deletedDoc = finalSearchResult.results.find(
      (r) => r.metadata.documentId === "integration-test-3"
    );
    expect(deletedDoc).toBeUndefined();

    // 8. 最終的なコレクション情報
    const finalInfo = await getCollectionInfo();
    expect(finalInfo.info.documentCount).toBe(2);
  });

  test("Search with filters", async () => {
    await indexDocuments({
      documents: testDocs,
      upsert: true,
    });

    // 言語フィルター
    const tsResult = await search({
      query: "service",
      k: 10,
      filter: { language: "typescript" },
    });

    expect(tsResult.success).toBe(true);
    expect(
      tsResult.results.every((r) => r.metadata.language === "typescript")
    ).toBe(true);

    // ファイルパスフィルター
    const pathResult = await search({
      query: "function",
      k: 10,
      filter: { filePath: "/test/services/userService.ts" },
    });

    expect(pathResult.success).toBe(true);
    expect(
      pathResult.results.every(
        (r) => r.metadata.filePath === "/test/services/userService.ts"
      )
    ).toBe(true);
  });

  test("Error handling", async () => {
    // 空のドキュメント配列
    await expect(
      indexDocuments({
        documents: [],
      })
    ).rejects.toThrow();

    // 無効な検索クエリ（空文字列）
    const emptySearchResult = await search({
      query: "",
      k: 5,
    });
    expect(emptySearchResult.success).toBe(true);
    // 空クエリでも何らかの結果が返る可能性がある

    // 存在しないIDの削除（エラーにならずに成功する）
    const deleteNonExistentResult = await deleteDocuments({
      ids: ["non-existent-id-xyz"],
    });
    expect(deleteNonExistentResult.success).toBe(true);
  });
});
```

### 4. パフォーマンステストの作成

```typescript
// tests/performance/benchmark.test.ts
import { indexDocuments } from "../../src/tools/indexDocuments";
import { search } from "../../src/tools/search";
import { closeVectorStore } from "../../src/utils/vectorStore";

describe("Performance Benchmarks", () => {
  afterAll(async () => {
    await closeVectorStore();
  });

  test("should index 100 documents in reasonable time", async () => {
    const docs = Array.from({ length: 100 }, (_, i) => ({
      id: `perf-test-${i}`,
      content: `This is test document number ${i}. It contains some sample text for performance testing.`,
      metadata: {
        filePath: `/test/perf/doc${i}.txt`,
        language: "text",
      },
    }));

    const startTime = Date.now();

    const result = await indexDocuments({
      documents: docs,
      upsert: false,
    });

    const duration = Date.now() - startTime;

    expect(result.success).toBe(true);
    expect(result.indexed).toBe(100);
    expect(duration).toBeLessThan(30000); // 30秒以内

    console.log(`Indexed 100 documents in ${duration}ms`);
  }, 60000); // 60秒のタイムアウト

  test("should perform 100 searches in reasonable time", async () => {
    // まずドキュメントをインデックス
    const docs = Array.from({ length: 50 }, (_, i) => ({
      id: `search-perf-${i}`,
      content: `Sample document ${i} with various keywords like user, database, authentication, service, and API.`,
      metadata: {
        filePath: `/test/search/doc${i}.txt`,
      },
    }));

    await indexDocuments({ documents: docs, upsert: false });

    const queries = [
      "user authentication",
      "database connection",
      "API service",
      "error handling",
      "data processing",
    ];

    const startTime = Date.now();

    for (let i = 0; i < 100; i++) {
      const query = queries[i % queries.length];
      await search({ query, k: 5 });
    }

    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(20000); // 20秒以内

    console.log(`Performed 100 searches in ${duration}ms`);
  }, 60000);
});
```

### 5. package.jsonにテストスクリプトを追加

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:unit": "jest --testPathPattern=tests/.*\\.test\\.ts --testPathIgnorePatterns=integration",
    "test:integration": "jest --testPathPattern=tests/integration",
    "test:performance": "jest --testPathPattern=tests/performance"
  }
}
```

### 6. CI/CD用のテスト設定

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm run test:coverage

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

## 完了条件

- [ ] jest.config.jsが最適化されている
- [ ] tests/setup.tsが作成されている
- [ ] 統合テストが実装されている
- [ ] パフォーマンステストが実装されている
- [ ] 全てのツールにユニットテストがある
- [ ] テストカバレッジが70%以上
- [ ] 全てのテストがパスする
- [ ] CI/CD設定がある（オプション）

## 動作確認

### 全テストの実行

```bash
npm run test
```

### カバレッジレポートの生成

```bash
npm run test:coverage
```

結果は `coverage/` ディレクトリに出力される。

### ユニットテストのみ実行

```bash
npm run test:unit
```

### 統合テストのみ実行

```bash
npm run test:integration
```

### パフォーマンステストのみ実行

```bash
npm run test:performance
```

### ウォッチモード（開発時）

```bash
npm run test:watch
```

## テストのベストプラクティス

- テストは独立して実行可能にする
- テストデータは各テストでクリーンアップ
- 非同期処理は適切に待機
- エッジケースもテストする
- パフォーマンス要件を明確にする

## トラブルシューティング

- テストがタイムアウトする: testTimeoutを増やす
- カバレッジが低い: 未テストのファイルを確認
- テストが不安定: 非同期処理の待機を確認

## 次のタスク

タスク14: ドキュメントの作成
