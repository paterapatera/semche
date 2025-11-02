// src/utils/vectorStore.ts
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { HuggingFaceTransformersEmbeddings } from "@langchain/community/embeddings/huggingface_transformers";
import { config } from "../config.js";
import fs from "fs";

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
    model: config.embeddingModel,
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
