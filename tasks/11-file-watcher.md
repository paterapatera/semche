# タスク11: ファイル監視機能の実装

## 目的

chokidarを使用してファイルシステムを監視し、ファイルの変更を自動的にベクトルストアに反映する機能を実装する

## 作業内容

### 1. ファイルウォッチャーの作成

```typescript
// src/utils/fileWatcher.ts
import chokidar from "chokidar";
import fs from "fs";
import path from "path";
import { indexDocuments } from "../tools/indexDocuments.js";
import { deleteDocuments } from "../tools/deleteDocuments.js";
import { logger } from "./logger.js";
import { config } from "../config.js";

let watcher: chokidar.FSWatcher | null = null;

/**
 * ファイルの言語を拡張子から推測
 */
function detectLanguage(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  const languageMap: Record<string, string> = {
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".py": "python",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
  };

  return languageMap[ext] || "text";
}

/**
 * ファイルをインデックス
 */
async function indexFile(filePath: string): Promise<void> {
  try {
    logger.info(`Indexing file: ${filePath}`);

    const content = fs.readFileSync(filePath, "utf-8");
    const language = detectLanguage(filePath);

    await indexDocuments({
      documents: [
        {
          content,
          metadata: {
            filePath,
            language,
            projectName: config.watchProjectName,
          },
        },
      ],
      upsert: true, // 既存のファイルは更新
    });

    logger.info(`Successfully indexed: ${filePath}`);
  } catch (error) {
    logger.error(`Failed to index file: ${filePath}`, error);
  }
}

/**
 * ファイルを削除
 */
async function removeFile(filePath: string): Promise<void> {
  try {
    logger.info(`Removing file from index: ${filePath}`);

    await deleteDocuments({
      filter: { filePath },
    });

    logger.info(`Successfully removed: ${filePath}`);
  } catch (error) {
    logger.error(`Failed to remove file: ${filePath}`, error);
  }
}

/**
 * ファイル監視を開始
 */
export function startFileWatcher(): void {
  if (!config.watchEnabled) {
    logger.info("File watching is disabled");
    return;
  }

  if (watcher) {
    logger.warn("File watcher is already running");
    return;
  }

  const watchPaths = config.watchPaths || [process.cwd()];
  const watchPatterns = config.watchPatterns || [
    "**/*.ts",
    "**/*.tsx",
    "**/*.js",
    "**/*.jsx",
    "**/*.py",
  ];

  const ignorePatterns = config.watchIgnorePatterns || [
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/.git/**",
    "**/coverage/**",
    "**/*.test.*",
    "**/*.spec.*",
  ];

  logger.info("Starting file watcher...");
  logger.info(`Watch paths: ${watchPaths.join(", ")}`);
  logger.info(`Patterns: ${watchPatterns.join(", ")}`);
  logger.info(`Ignore: ${ignorePatterns.join(", ")}`);

  watcher = chokidar.watch(watchPatterns, {
    cwd: watchPaths[0],
    ignored: ignorePatterns,
    persistent: true,
    ignoreInitial: config.watchInitialScan === false,
    awaitWriteFinish: {
      stabilityThreshold: 2000,
      pollInterval: 100,
    },
  });

  // ファイル追加イベント
  watcher.on("add", async (relativePath) => {
    const fullPath = path.resolve(watchPaths[0], relativePath);
    logger.info(`File added: ${fullPath}`);
    await indexFile(fullPath);
  });

  // ファイル変更イベント
  watcher.on("change", async (relativePath) => {
    const fullPath = path.resolve(watchPaths[0], relativePath);
    logger.info(`File changed: ${fullPath}`);
    await indexFile(fullPath);
  });

  // ファイル削除イベント
  watcher.on("unlink", async (relativePath) => {
    const fullPath = path.resolve(watchPaths[0], relativePath);
    logger.info(`File deleted: ${fullPath}`);
    await removeFile(fullPath);
  });

  // エラーイベント
  watcher.on("error", (error) => {
    logger.error("File watcher error", error);
  });

  // 準備完了イベント
  watcher.on("ready", () => {
    logger.info("File watcher is ready and watching for changes");
  });
}

/**
 * ファイル監視を停止
 */
export async function stopFileWatcher(): Promise<void> {
  if (!watcher) {
    logger.warn("File watcher is not running");
    return;
  }

  logger.info("Stopping file watcher...");
  await watcher.close();
  watcher = null;
  logger.info("File watcher stopped");
}

/**
 * 監視状態を取得
 */
export function isWatching(): boolean {
  return watcher !== null;
}
```

### 2. 設定ファイルに監視設定を追加

```typescript
// src/config.ts (Config インターフェースを拡張)
export interface Config {
  // ... 既存の設定 ...

  // ファイル監視設定
  watchEnabled: boolean;
  watchPaths?: string[];
  watchPatterns?: string[];
  watchIgnorePatterns?: string[];
  watchInitialScan?: boolean;
  watchProjectName?: string;
}

export const config: Config = {
  // ... 既存の設定 ...

  // ファイル監視
  watchEnabled: process.env.WATCH_ENABLED === "true",
  watchPaths: process.env.WATCH_PATHS?.split(","),
  watchPatterns: process.env.WATCH_PATTERNS?.split(","),
  watchIgnorePatterns: process.env.WATCH_IGNORE_PATTERNS?.split(","),
  watchInitialScan: process.env.WATCH_INITIAL_SCAN !== "false",
  watchProjectName: process.env.WATCH_PROJECT_NAME,
};
```

### 3. .env.exampleに監視設定を追加

```bash
# ファイル監視設定（オプション）
WATCH_ENABLED=false
WATCH_PATHS=./src,./lib
WATCH_PATTERNS=**/*.ts,**/*.tsx,**/*.js,**/*.jsx
WATCH_IGNORE_PATTERNS=**/node_modules/**,**/dist/**,**/.git/**
WATCH_INITIAL_SCAN=true
WATCH_PROJECT_NAME=my-project
```

### 4. MCPサーバーに統合

```typescript
// src/index.ts (main関数を更新)
import { startFileWatcher, stopFileWatcher } from "./utils/fileWatcher.js";

async function main() {
  logger.info("Starting Semche MCP Server...");
  logger.info(`Collection: ${config.collectionName}`);
  logger.info(`Persist Directory: ${config.persistDirectory}`);

  // ベクトルストアの初期化
  try {
    await getVectorStore();
    logger.info("Vector store initialized successfully");
  } catch (error) {
    logger.error("Failed to initialize vector store", error);
    throw error;
  }

  // ファイル監視の開始（有効な場合）
  if (config.watchEnabled) {
    startFileWatcher();
  }

  // stdioトランスポートでサーバー起動
  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info("Semche MCP Server is running");

  // グレースフルシャットダウン
  const shutdown = async () => {
    logger.info("Shutting down server...");
    await stopFileWatcher();
    await closeVectorStore();
    await server.close();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}
```

### 5. テストの作成

```typescript
// tests/utils/fileWatcher.test.ts
import {
  startFileWatcher,
  stopFileWatcher,
  isWatching,
} from "../../src/utils/fileWatcher";
import { search } from "../../src/tools/search";
import { getVectorStore, closeVectorStore } from "../../src/utils/vectorStore";
import fs from "fs";
import path from "path";

// テスト用の一時ディレクトリ
const TEST_DIR = path.join(__dirname, "../temp-watch-test");
const TEST_FILE = path.join(TEST_DIR, "test-file.ts");

describe("FileWatcher", () => {
  beforeAll(() => {
    // テストディレクトリの作成
    if (!fs.existsSync(TEST_DIR)) {
      fs.mkdirSync(TEST_DIR, { recursive: true });
    }
  });

  afterAll(async () => {
    await stopFileWatcher();
    await closeVectorStore();

    // テストディレクトリの削除
    if (fs.existsSync(TEST_DIR)) {
      fs.rmSync(TEST_DIR, { recursive: true, force: true });
    }
  });

  test("should start and stop file watcher", async () => {
    // 監視設定を有効化（環境変数で設定）
    process.env.WATCH_ENABLED = "true";
    process.env.WATCH_PATHS = TEST_DIR;

    startFileWatcher();
    expect(isWatching()).toBe(true);

    await stopFileWatcher();
    expect(isWatching()).toBe(false);
  });

  test("should index new files automatically", async () => {
    // 監視開始
    process.env.WATCH_ENABLED = "true";
    process.env.WATCH_PATHS = TEST_DIR;
    startFileWatcher();

    // ファイル作成
    const testContent = "export function testFunction() { return 42; }";
    fs.writeFileSync(TEST_FILE, testContent);

    // インデックスされるまで待機
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // 検索して確認
    const result = await search({
      query: "testFunction",
      k: 5,
    });

    expect(result.results.length).toBeGreaterThan(0);
    expect(result.results[0].content).toContain("testFunction");

    await stopFileWatcher();
  });

  test("should update index when files change", async () => {
    // 監視開始
    process.env.WATCH_ENABLED = "true";
    process.env.WATCH_PATHS = TEST_DIR;
    startFileWatcher();

    // ファイル作成
    fs.writeFileSync(TEST_FILE, "export const original = true;");
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // ファイル更新
    fs.writeFileSync(TEST_FILE, "export const updated = true;");
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // 検索して確認
    const result = await search({
      query: "updated",
      k: 5,
    });

    expect(result.results.length).toBeGreaterThan(0);
    expect(result.results[0].content).toContain("updated");

    await stopFileWatcher();
  });

  test("should remove index when files are deleted", async () => {
    // 監視開始
    process.env.WATCH_ENABLED = "true";
    process.env.WATCH_PATHS = TEST_DIR;
    startFileWatcher();

    // ファイル作成
    fs.writeFileSync(TEST_FILE, "export const toBeDeleted = true;");
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // ファイル削除
    fs.unlinkSync(TEST_FILE);
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // 検索して削除を確認
    const result = await search({
      query: "toBeDeleted",
      k: 5,
      filter: { filePath: TEST_FILE },
    });

    expect(result.results.length).toBe(0);

    await stopFileWatcher();
  });
});
```

## 完了条件

- [ ] src/utils/fileWatcher.tsが実装されている
- [ ] configに監視設定が追加されている
- [ ] .env.exampleに監視設定が追加されている
- [ ] MCPサーバーに統合されている
- [ ] ファイル追加時に自動インデックスされる
- [ ] ファイル変更時に自動更新される
- [ ] ファイル削除時にインデックスから削除される
- [ ] テストが全てパスする

## 動作確認

### ローカルテスト

```bash
npm run test -- tests/utils/fileWatcher.test.ts
```

### 実際の使用での確認

1. .envで監視を有効化:

   ```
   WATCH_ENABLED=true
   WATCH_PATHS=./src
   WATCH_PATTERNS=**/*.ts,**/*.js
   ```

2. サーバーを起動: `npm run dev`

3. 監視対象ディレクトリのファイルを編集

4. ログで自動インデックスを確認:

   ```
   [INFO] File changed: /path/to/file.ts
   [INFO] Indexing file: /path/to/file.ts
   [INFO] Successfully indexed: /path/to/file.ts
   ```

5. Cursor IDEで検索して反映を確認

## パフォーマンスの考慮

- `awaitWriteFinish`オプションでファイル書き込み完了を待機
- 初期スキャンは大量のファイルがある場合に時間がかかる可能性
- `WATCH_INITIAL_SCAN=false`で初期スキャンを無効化可能

## トラブルシューティング

- ファイルがインデックスされない: watchPatternsを確認
- 不要なファイルがインデックスされる: ignoreパターンを追加
- パフォーマンスが悪い: watch対象を絞り込む

## 次のタスク

タスク12: エラーハンドリングとロギングの強化
