// src/config.ts
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

export interface Config {
  // ChromaDB設定
  persistDirectory: string;
  collectionName: string;

  // 埋め込みモデル設定
  embeddingModel: string;
  embeddingDimension: number;

  // HNSW設定
  hnswSpace: "cosine" | "l2" | "ip";
  hnswConstructionEf: number;
  hnswM: number;

  // その他
  anonymizedTelemetry: boolean;
  logLevel: string;

  // ファイルウォッチャー（オプション）
  enableFileWatcher: boolean;
  workspaceRoot: string;
}

export const config: Config = {
  persistDirectory: path.resolve(
    process.env.CHROMA_PERSIST_DIRECTORY || "./data/chroma"
  ),
  collectionName: process.env.CHROMA_COLLECTION_NAME || "semche_documents",
  embeddingModel:
    process.env.EMBEDDING_MODEL ||
    "sentence-transformers/stsb-xlm-r-multilingual",
  embeddingDimension: parseInt(process.env.EMBEDDING_DIMENSION || "768"),
  hnswSpace:
    (process.env.CHROMA_HNSW_SPACE as "cosine" | "l2" | "ip") || "cosine",
  hnswConstructionEf: parseInt(
    process.env.CHROMA_HNSW_CONSTRUCTION_EF || "100"
  ),
  hnswM: parseInt(process.env.CHROMA_HNSW_M || "16"),
  anonymizedTelemetry: process.env.CHROMA_ANONYMIZED_TELEMETRY === "true",
  logLevel: process.env.LOG_LEVEL || "info",
  enableFileWatcher: process.env.ENABLE_FILE_WATCHER === "true",
  workspaceRoot: process.env.WORKSPACE_ROOT || "./",
};

// 設定の検証
export function validateConfig(): void {
  const required = ["persistDirectory", "collectionName"];

  for (const key of required) {
    if (!config[key as keyof Config]) {
      throw new Error(`Missing required configuration: ${key}`);
    }
  }

  if (config.embeddingDimension <= 0) {
    throw new Error("Invalid EMBEDDING_DIMENSION");
  }

  if (!["cosine", "l2", "ip"].includes(config.hnswSpace)) {
    throw new Error("Invalid CHROMA_HNSW_SPACE");
  }

  console.error("[Semche] Configuration validated successfully");
  console.error(`[Semche] Persist directory: ${config.persistDirectory}`);
  console.error(`[Semche] Collection name: ${config.collectionName}`);
}
