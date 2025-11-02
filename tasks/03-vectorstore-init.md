# タスク3: ChromaDBベクトルストアの初期化

## 目的

ChromaDBとHuggingFace埋め込みモデルを初期化し、ベクトルストアを構築する

## 作業内容

### 1. ベクトルストア初期化モジュールの作成

```typescript
// src/utils/vectorStore.ts
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { HuggingFaceTransformersEmbeddings } from "@langchain/community/embeddings/hf_transformers";
import { config } from "../config.js";
import fs from "fs";
import path from "path";

let vectorStoreInstance: Chroma | null = null;

/**
 * ベクトルストアのシングルトンインスタンスを取得
 */
export async function getVectorStore(): Promise<Chroma> {
  if (vectorStoreInstance) {
    return vectorStoreInstance;
  }

  console.error("[Semche] Initializing vector store...");

  // データディレクトリの作成
  if (!fs.existsSync(config.persistDirectory)) {
    console.error(
      `[Semche] Creating persist directory: ${config.persistDirectory}`
    );
    fs.mkdirSync(config.persistDirectory, { recursive: true });
  }

  // 埋め込みモデルの初期化
  const embeddings = new HuggingFaceTransformersEmbeddings({
    modelName: config.embeddingModel,
  });

  console.error(`[Semche] Loading embedding model: ${config.embeddingModel}`);

  // ChromaDBの初期化
  vectorStoreInstance = new Chroma(embeddings, {
    collectionName: config.collectionName,
    url: undefined, // ローカルモード
    collectionMetadata: {
      "hnsw:space": config.hnswSpace,
      "hnsw:construction_ef": config.hnswConstructionEf,
      "hnsw:M": config.hnswM,
    },
  });

  console.error(
    `[Semche] Vector store initialized with collection: ${config.collectionName}`
  );

  return vectorStoreInstance;
}

/**
 * ベクトルストアをクリーンアップ
 */
export async function closeVectorStore(): Promise<void> {
  if (vectorStoreInstance) {
    console.error("[Semche] Closing vector store...");
    // Chromaには明示的なclose処理がないため、インスタンスをクリア
    vectorStoreInstance = null;
  }
}

/**
 * コレクション情報を取得
 */
export async function getCollectionStats(): Promise<{
  documentCount: number;
  collectionName: string;
  embeddingDimension: number;
}> {
  const vectorStore = await getVectorStore();

  // ChromaDBから統計情報を取得
  // 注: LangChainのChromaラッパーでは直接カウントできないため、
  // 実際の実装ではChromaクライアントを直接使用する必要がある場合がある

  return {
    documentCount: 0, // TODO: 実装が必要
    collectionName: config.collectionName,
    embeddingDimension: config.embeddingDimension,
  };
}
```

### 2. エラーハンドリングとロギングの追加

```typescript
// src/utils/logger.ts
export enum LogLevel {
  ERROR = "error",
  WARN = "warn",
  INFO = "info",
  DEBUG = "debug",
}

export function log(level: LogLevel, message: string, data?: any): void {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

  // MCPサーバーはstdoutを使用するため、ログはstderrに出力
  console.error(logMessage);

  if (data) {
    console.error(JSON.stringify(data, null, 2));
  }
}

export const logger = {
  error: (message: string, data?: any) => log(LogLevel.ERROR, message, data),
  warn: (message: string, data?: any) => log(LogLevel.WARN, message, data),
  info: (message: string, data?: any) => log(LogLevel.INFO, message, data),
  debug: (message: string, data?: any) => log(LogLevel.DEBUG, message, data),
};
```

### 3. テキスト分割ユーティリティの作成

```typescript
// src/utils/textSplitter.ts
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

export interface ChunkOptions {
  chunkSize?: number;
  chunkOverlap?: number;
  separators?: string[];
}

/**
 * テキストをチャンクに分割
 */
export async function splitText(
  text: string,
  options: ChunkOptions = {}
): Promise<string[]> {
  const {
    chunkSize = 1000,
    chunkOverlap = 200,
    separators = ["\n\n", "\n", " ", ""],
  } = options;

  const splitter = new RecursiveCharacterTextSplitter({
    chunkSize,
    chunkOverlap,
    separators,
  });

  return await splitter.splitText(text);
}

/**
 * コード用のテキスト分割（より適切なセパレータ）
 */
export async function splitCode(
  code: string,
  language: string,
  options: ChunkOptions = {}
): Promise<string[]> {
  const codeSeparators: Record<string, string[]> = {
    typescript: ["\n\nclass ", "\n\nfunction ", "\n\nexport ", "\n\n", "\n"],
    javascript: ["\n\nclass ", "\n\nfunction ", "\n\nexport ", "\n\n", "\n"],
    python: ["\n\nclass ", "\n\ndef ", "\n\n", "\n"],
    default: ["\n\n", "\n", " ", ""],
  };

  const separators = codeSeparators[language] || codeSeparators.default;

  return splitText(code, { ...options, separators });
}
```

### 4. 初期化テストの作成

```typescript
// tests/vectorStore.test.ts
import { getVectorStore, closeVectorStore } from "../src/utils/vectorStore";

describe("VectorStore", () => {
  afterAll(async () => {
    await closeVectorStore();
  });

  test("should initialize vector store", async () => {
    const vectorStore = await getVectorStore();
    expect(vectorStore).toBeDefined();
  });

  test("should return same instance (singleton)", async () => {
    const instance1 = await getVectorStore();
    const instance2 = await getVectorStore();
    expect(instance1).toBe(instance2);
  });
});
```

## 完了条件

- [ ] src/utils/vectorStore.tsが実装されている
- [ ] src/utils/logger.tsが実装されている
- [ ] src/utils/textSplitter.tsが実装されている
- [ ] 埋め込みモデルが正常にロードされる
- [ ] ChromaDBインスタンスが作成される
- [ ] データディレクトリが自動作成される
- [ ] テストが全てパスする

## 注意事項

- 初回起動時に埋め込みモデルのダウンロードに時間がかかる可能性がある
- モデルサイズは約400MBなので、ストレージ容量に注意

## 次のタスク

タスク4: MCPサーバーの基本セットアップ
