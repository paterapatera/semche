# タスク12: エラーハンドリングとロギングの強化

## 目的

堅牢なエラーハンドリングとログシステムを構築し、デバッグとトラブルシューティングを容易にする

## 作業内容

### 1. カスタムエラークラスの作成

```typescript
// src/utils/errors.ts
export class SemcheError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = "SemcheError";
    Error.captureStackTrace(this, this.constructor);
  }
}

export class VectorStoreError extends SemcheError {
  constructor(message: string, details?: any) {
    super(message, "VECTOR_STORE_ERROR", 500, details);
    this.name = "VectorStoreError";
  }
}

export class IndexingError extends SemcheError {
  constructor(message: string, details?: any) {
    super(message, "INDEXING_ERROR", 500, details);
    this.name = "IndexingError";
  }
}

export class SearchError extends SemcheError {
  constructor(message: string, details?: any) {
    super(message, "SEARCH_ERROR", 500, details);
    this.name = "SearchError";
  }
}

export class ConfigurationError extends SemcheError {
  constructor(message: string, details?: any) {
    super(message, "CONFIGURATION_ERROR", 500, details);
    this.name = "ConfigurationError";
  }
}

export class FileWatcherError extends SemcheError {
  constructor(message: string, details?: any) {
    super(message, "FILE_WATCHER_ERROR", 500, details);
    this.name = "FileWatcherError";
  }
}

/**
 * エラーを安全に文字列化
 */
export function serializeError(error: unknown): {
  message: string;
  code?: string;
  stack?: string;
  details?: any;
} {
  if (error instanceof SemcheError) {
    return {
      message: error.message,
      code: error.code,
      stack: error.stack,
      details: error.details,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      stack: error.stack,
    };
  }

  return {
    message: String(error),
  };
}
```

### 2. ログシステムの強化

```typescript
// src/utils/logger.ts (拡張版)
import fs from "fs";
import path from "path";

export enum LogLevel {
  ERROR = "error",
  WARN = "warn",
  INFO = "info",
  DEBUG = "debug",
}

const LOG_LEVELS: Record<LogLevel, number> = {
  [LogLevel.ERROR]: 0,
  [LogLevel.WARN]: 1,
  [LogLevel.INFO]: 2,
  [LogLevel.DEBUG]: 3,
};

interface LogConfig {
  level: LogLevel;
  logToFile: boolean;
  logFilePath?: string;
  maxLogFileSize?: number; // bytes
}

let logConfig: LogConfig = {
  level: (process.env.LOG_LEVEL as LogLevel) || LogLevel.INFO,
  logToFile: process.env.LOG_TO_FILE === "true",
  logFilePath: process.env.LOG_FILE_PATH || "./logs/semche.log",
  maxLogFileSize: 10 * 1024 * 1024, // 10MB
};

/**
 * ログをファイルに書き込む
 */
function writeToFile(message: string): void {
  if (!logConfig.logToFile || !logConfig.logFilePath) {
    return;
  }

  try {
    const logDir = path.dirname(logConfig.logFilePath);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    // ファイルサイズチェック（ローテーション）
    if (fs.existsSync(logConfig.logFilePath)) {
      const stats = fs.statSync(logConfig.logFilePath);
      if (stats.size > (logConfig.maxLogFileSize || 10485760)) {
        const timestamp = new Date().toISOString().replace(/:/g, "-");
        const backupPath = `${logConfig.logFilePath}.${timestamp}`;
        fs.renameSync(logConfig.logFilePath, backupPath);
      }
    }

    fs.appendFileSync(logConfig.logFilePath, message + "\n");
  } catch (error) {
    console.error("Failed to write to log file:", error);
  }
}

/**
 * ログレベルが有効かチェック
 */
function shouldLog(level: LogLevel): boolean {
  return LOG_LEVELS[level] <= LOG_LEVELS[logConfig.level];
}

/**
 * ログを出力
 */
export function log(level: LogLevel, message: string, data?: any): void {
  if (!shouldLog(level)) {
    return;
  }

  const timestamp = new Date().toISOString();
  let logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

  // stderrに出力（MCPサーバーはstdoutを使用するため）
  console.error(logMessage);

  if (data !== undefined) {
    const dataStr =
      typeof data === "object" ? JSON.stringify(data, null, 2) : String(data);
    console.error(dataStr);
    logMessage += "\n" + dataStr;
  }

  // ファイルにも書き込み
  writeToFile(logMessage);
}

export const logger = {
  error: (message: string, data?: any) => log(LogLevel.ERROR, message, data),
  warn: (message: string, data?: any) => log(LogLevel.WARN, message, data),
  info: (message: string, data?: any) => log(LogLevel.INFO, message, data),
  debug: (message: string, data?: any) => log(LogLevel.DEBUG, message, data),

  /**
   * ログ設定を更新
   */
  configure: (config: Partial<LogConfig>) => {
    logConfig = { ...logConfig, ...config };
  },
};
```

### 3. ツールでのエラーハンドリング強化

```typescript
// src/tools/indexDocuments.ts (エラーハンドリング追加)
import { IndexingError, serializeError } from "../utils/errors.js";

export async function indexDocuments(options: IndexDocumentsOptions): Promise<{
  success: boolean;
  indexed: number;
  updated: number;
  chunks: number;
  errors?: any[];
  message: string;
}> {
  const { documents, upsert = true } = options;

  if (!documents || documents.length === 0) {
    throw new IndexingError("No documents provided for indexing");
  }

  logger.info(`Indexing ${documents.length} document(s), upsert: ${upsert}`);

  const errors: any[] = [];

  try {
    const vectorStore = await getVectorStore();

    let totalIndexed = 0;
    let totalUpdated = 0;
    let totalChunks = 0;

    for (const doc of documents) {
      try {
        // ドキュメント処理ロジック...
        // (既存のコードはそのまま)
      } catch (docError) {
        logger.error(
          `Failed to index document: ${doc.id || "unknown"}`,
          docError
        );
        errors.push({
          documentId: doc.id,
          error: serializeError(docError),
        });
        // エラーがあっても続行
        continue;
      }
    }

    const hasErrors = errors.length > 0;
    const message = hasErrors
      ? `Indexed ${totalIndexed} documents with ${errors.length} error(s)`
      : `Successfully indexed ${totalIndexed} new and updated ${totalUpdated} existing documents (${totalChunks} chunks total)`;

    return {
      success: errors.length === 0,
      indexed: totalIndexed,
      updated: totalUpdated,
      chunks: totalChunks,
      errors: errors.length > 0 ? errors : undefined,
      message,
    };
  } catch (error) {
    logger.error("Failed to index documents", error);
    throw new IndexingError("Indexing operation failed", serializeError(error));
  }
}
```

### 4. グローバルエラーハンドラーの追加

```typescript
// src/index.ts (エラーハンドリング追加)
import { serializeError } from "./utils/errors.js";

// 未処理の例外をキャッチ
process.on("uncaughtException", (error) => {
  logger.error("Uncaught Exception", serializeError(error));
  // クリーンアップ
  closeVectorStore()
    .then(() => {
      process.exit(1);
    })
    .catch(() => {
      process.exit(1);
    });
});

// 未処理のPromise拒否をキャッチ
process.on("unhandledRejection", (reason) => {
  logger.error("Unhandled Rejection", serializeError(reason));
});

// MCPツール呼び出しのエラーハンドリング強化
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  logger.info(`Tool called: ${name}`, args);

  try {
    // ... 既存のツール呼び出しロジック ...
  } catch (error) {
    logger.error(`Tool execution failed: ${name}`, serializeError(error));

    const errorInfo = serializeError(error);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              error: errorInfo.message,
              code: errorInfo.code,
              details: errorInfo.details,
            },
            null,
            2
          ),
        },
      ],
      isError: true,
    };
  }
});
```

### 5. .env.exampleにログ設定を追加

```bash
# ログ設定
LOG_LEVEL=info  # debug, info, warn, error
LOG_TO_FILE=false
LOG_FILE_PATH=./logs/semche.log
```

### 6. テストの作成

```typescript
// tests/utils/errors.test.ts
import {
  SemcheError,
  VectorStoreError,
  IndexingError,
  serializeError,
} from "../../src/utils/errors";

describe("Custom Errors", () => {
  test("should create SemcheError", () => {
    const error = new SemcheError("Test error", "TEST_ERROR", 500, {
      detail: "test",
    });

    expect(error.message).toBe("Test error");
    expect(error.code).toBe("TEST_ERROR");
    expect(error.statusCode).toBe(500);
    expect(error.details).toEqual({ detail: "test" });
  });

  test("should create VectorStoreError", () => {
    const error = new VectorStoreError("Vector store failed");

    expect(error.name).toBe("VectorStoreError");
    expect(error.code).toBe("VECTOR_STORE_ERROR");
  });

  test("should serialize SemcheError", () => {
    const error = new IndexingError("Indexing failed", { docId: "123" });
    const serialized = serializeError(error);

    expect(serialized.message).toBe("Indexing failed");
    expect(serialized.code).toBe("INDEXING_ERROR");
    expect(serialized.details).toEqual({ docId: "123" });
    expect(serialized.stack).toBeDefined();
  });

  test("should serialize standard Error", () => {
    const error = new Error("Standard error");
    const serialized = serializeError(error);

    expect(serialized.message).toBe("Standard error");
    expect(serialized.stack).toBeDefined();
  });

  test("should serialize unknown error types", () => {
    const serialized = serializeError("String error");

    expect(serialized.message).toBe("String error");
  });
});
```

## 完了条件

- [ ] src/utils/errors.tsが実装されている
- [ ] ロガーが強化されている（ファイル出力、ローテーション）
- [ ] 全てのツールでエラーハンドリングが実装されている
- [ ] グローバルエラーハンドラーが追加されている
- [ ] .env.exampleにログ設定が追加されている
- [ ] エラーメッセージが明確で実用的
- [ ] テストが全てパスする

## 動作確認

### エラーハンドリングのテスト

```bash
npm run test -- tests/utils/errors.test.ts
```

### ログレベルの確認

```bash
# DEBUGレベルで起動
LOG_LEVEL=debug npm run dev

# ERRORのみ表示
LOG_LEVEL=error npm run dev
```

### ファイルログの確認

```bash
# ログファイル出力を有効化
LOG_TO_FILE=true LOG_FILE_PATH=./logs/semche.log npm run dev

# ログファイルを確認
cat ./logs/semche.log
```

## エラーの種類と用途

### SemcheError

- 基底エラークラス
- カスタムエラーコードとステータスコード

### VectorStoreError

- ベクトルストアの初期化失敗
- データベース接続エラー

### IndexingError

- ドキュメントのインデックス失敗
- チャンク分割エラー

### SearchError

- 検索クエリエラー
- フィルター処理エラー

### ConfigurationError

- 設定値の検証失敗
- 環境変数の不足

### FileWatcherError

- ファイル監視の開始失敗
- ファイル読み込みエラー

## トラブルシューティング

- ログファイルが作成されない: ディレクトリの書き込み権限を確認
- エラーが多すぎる: LOG_LEVELをwarnまたはerrorに変更
- スタックトレースが見えない: LOG_LEVEL=debugで詳細表示

## 次のタスク

タスク13: テストスイートの完成
