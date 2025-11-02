# タスク2: 環境変数とディレクトリ構造の設定

## 目的

環境変数の管理とデータストレージの構造を定義する

## 作業内容

### 1. .env.exampleファイルの作成

```bash
# ChromaDBデータ保存先（必須）
CHROMA_PERSIST_DIRECTORY=./data/chroma

# コレクション名（必須）
CHROMA_COLLECTION_NAME=semche_documents

# 埋め込みモデル設定
EMBEDDING_MODEL=sentence-transformers/stsb-xlm-r-multilingual
EMBEDDING_DIMENSION=768

# ChromaDB HNSW設定
CHROMA_HNSW_SPACE=cosine
CHROMA_HNSW_CONSTRUCTION_EF=100
CHROMA_HNSW_M=16

# その他設定
CHROMA_ANONYMIZED_TELEMETRY=false
LOG_LEVEL=info

# ファイルウォッチャー設定（オプション）
ENABLE_FILE_WATCHER=false
WORKSPACE_ROOT=./
```

### 2. .gitignoreファイルの作成

```gitignore
# 環境変数ファイル
.env
.env.local
.env.*.local

# データディレクトリ
data/
*.sqlite3

# ビルド出力
dist/
build/

# 依存関係
node_modules/

# ログファイル
logs/
*.log
npm-debug.log*

# IDE設定
.vscode/
.idea/
*.swp
*.swo
*.code-workspace

# OS固有
.DS_Store
Thumbs.db

# テスト関連
coverage/
.nyc_output/

# その他
*.tsbuildinfo
.semche/
```

### 3. データディレクトリ構造の定義

プロジェクトルートに以下の構造を作成：

```
semche/
├── data/
│   └── chroma/           # ChromaDBデータ（gitignore対象）
│       ├── chroma.sqlite3
│       └── index/
├── src/
│   ├── index.ts          # MCPサーバーエントリーポイント
│   ├── config.ts         # 環境変数読み込み
│   ├── tools/            # MCPツール実装
│   ├── resources/        # MCPリソース実装
│   ├── prompts/          # MCPプロンプト実装
│   └── utils/            # ユーティリティ関数
├── tests/                # テストファイル
├── tasks/                # タスク管理
├── .env.example
├── .gitignore
├── package.json
├── tsconfig.json
└── README.md
```

### 4. 環境変数読み込み用のconfig.tsを作成

```typescript
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
```

### 5. 実際の.envファイルを作成（ローカル開発用）

```bash
cp .env.example .env
# 必要に応じて設定値を編集
```

## 完了条件

- [ ] .env.exampleが作成されている
- [ ] .gitignoreが設定されている
- [ ] データディレクトリ構造が作成されている
- [ ] src/config.tsが実装されている
- [ ] ローカルの.envファイルが作成されている
- [ ] config.tsで環境変数が正しく読み込める

## 次のタスク

タスク3: ChromaDBベクトルストアの初期化
