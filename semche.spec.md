# Semche - ベクトル検索システム仕様書

## 1. 概要

Semcheは、LangChainとTypeScriptを使用したベクトル検索システムです。テキストデータをベクトル化し、意味的な類似性に基づいて効率的な検索を実現します。MCPサーバーとして実装され、Cursor IDEから直接利用できます。

## 2. 技術スタック

- **言語**: TypeScript
- **プロトコル**: MCP (Model Context Protocol)
- **対象クライアント**: Cursor IDE
- **フレームワーク**: LangChain
- **埋め込みモデル**: sentence-transformers/stsb-xlm-r-multilingual
- **ベクトルストア**: ChromaDB（ローカル永続化）
- **データ保存**: ローカルファイルシステム
- **設定管理**: .env（環境変数）

## 3. システムアーキテクチャ

### 3.1 コンポーネント構成

```
┌─────────────────┐
│   入力データ    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  テキスト処理   │
│  (Chunking)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  埋め込み生成   │
│  (Embedding)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ベクトルストア  │
│   (Storage)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  類似度検索     │
│  (Retrieval)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   検索結果      │
└─────────────────┘
```

### 3.2 MCPサーバーアーキテクチャ

```
┌─────────────────────────────────────────┐
│              Cursor IDE                 │
│  (コード編集 + AI アシスタント)         │
└──────────────────┬──────────────────────┘
                   │ MCP Protocol
                   │ (stdio)
                   ▼
┌─────────────────────────────────────────┐
│           Semche MCPサーバー            │
├─────────────────────────────────────────┤
│  Tools (MCPツール)                      │
│  ├─ indexDocuments                      │
│  │   └─ コードベースのインデックス化   │
│  ├─ search                              │
│  │   └─ セマンティックコード検索       │
│  ├─ deleteDocuments                     │
│  │   └─ 古いドキュメントの削除         │
│  └─ getCollectionInfo                   │
│      └─ インデックス統計情報           │
├─────────────────────────────────────────┤
│  Resources (リソース)                   │
│  ├─ collection://stats                  │
│  │   └─ プロジェクト統計               │
│  └─ collection://documents              │
│      └─ インデックス済みファイル一覧   │
├─────────────────────────────────────────┤
│  Prompts (プロンプトテンプレート)        │
│  ├─ semantic-search                     │
│  │   └─ コード検索用プロンプト         │
│  └─ code-explanation                    │
│      └─ コード説明用プロンプト         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│        LangChain + ChromaDB             │
│     (ローカルベクトルストレージ)         │
└─────────────────────────────────────────┘
```

### 3.3 ChromaDBストレージ構成

#### ディレクトリ構造

```
project-root/
├── .env                  # 環境変数設定ファイル
├── mcp-config.json       # MCP設定ファイル
├── data/                 # データ保存ディレクトリ（.envで変更可能）
│   └── chroma/          # ChromaDBのデータディレクトリ
│       ├── chroma.sqlite3
│       └── index/
└── src/
    ├── index.ts         # MCPサーバーのエントリーポイント
    ├── tools/           # MCPツール実装
    ├── resources/       # MCPリソース実装
    └── prompts/         # MCPプロンプト実装
```

#### データの永続化

- **保存場所**: 環境変数で指定（デフォルト: `./data/chroma`）
- **データベース**: SQLite（メタデータ管理）
- **インデックス**: HNSW（高速近似最近傍探索）
- **自動保存**: 変更時に自動的に永続化

#### 環境変数設定（.env）

```bash
# ChromaDBデータ保存先
CHROMA_PERSIST_DIRECTORY=./data/chroma

# コレクション名
CHROMA_COLLECTION_NAME=semche_documents

# 埋め込みモデル設定
EMBEDDING_MODEL=sentence-transformers/stsb-xlm-r-multilingual
EMBEDDING_DIMENSION=768

# ChromaDB HNSW設定
CHROMA_HNSW_SPACE=cosine              # cosine, l2, ip
CHROMA_HNSW_CONSTRUCTION_EF=100
CHROMA_HNSW_M=16

# その他設定
CHROMA_ANONYMIZED_TELEMETRY=false
LOG_LEVEL=info
```

## 4. 機能要件

### 4.1 MCP機能（Cursor向け）

#### MCPツール（Tools）

- `indexDocuments`: プロジェクトファイルのインデックス化
  - コード、ドキュメント、設定ファイルなど
  - Cursorワークスペース内のファイルを対象
  - upsert動作：既存ファイルは自動更新、新規ファイルは追加
- `search`: セマンティックコード検索の実行
  - 自然言語でのコード検索
  - 関数、クラス、パターンの検索
- `deleteDocuments`: 古いインデックスの削除
  - 削除されたファイルのクリーンアップ
- `getCollectionInfo`: プロジェクトインデックス情報の取得
  - インデックス済みファイル数
  - 最終更新日時

#### MCPリソース（Resources）

- `collection://stats`: プロジェクト統計情報
  - インデックス済みファイル数
  - コード行数、言語分布
- `collection://documents`: インデックス済みファイル一覧
  - ファイルパス、更新日時
- `collection://config`: 現在の設定情報
  - ベクトルストアパス、モデル設定

#### MCPプロンプト（Prompts）

- `semantic-search`: セマンティックコード検索用プロンプト
  - 自然言語からコード検索へ変換
- `code-explanation`: コード説明用プロンプト
  - 検索結果の説明生成
- `similar-code`: 類似コード検索用プロンプト
  - 指定コードと類似したパターンの検索

### 4.2 ドキュメントインデックス機能

- プロジェクトファイルの読み込み
- コード構造を考慮したチャンク分割
- ベクトル埋め込みの生成
- ベクトルストアへの保存
- ファイルメタデータの保存（パス、言語、更新日時）

### 4.3 検索機能

- クエリテキストのベクトル化
- 類似度スコアに基づく検索
- Top-K検索結果の取得
- メタデータフィルタリング

### 4.4 管理機能

- インデックスの作成・更新・削除
- ドキュメントの追加・削除
- 検索統計の取得

## 5. データモデル

### 5.1 ドキュメント

```typescript
interface Document {
  id: string;
  content: string;
  metadata: {
    source: string;
    timestamp: Date;
    [key: string]: any;
  };
}
```

### 5.2 検索結果

```typescript
interface SearchResult {
  document: Document;
  score: number;
  rank: number;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
  executionTime: number;
}
```

## 6. 埋め込みモデル詳細

### 6.1 sentence-transformers/stsb-xlm-r-multilingual

- **タイプ**: 多言語対応sentence-transformersモデル
- **次元数**: 768
- **対応言語**: 多言語（日本語、英語を含む）
- **用途**: 文の意味的類似性の計算
- **特徴**:
  - 多言語間での類似度計算が可能
  - セマンティック検索に最適化
  - ゼロショット学習対応

### 6.2 埋め込み生成設定

```typescript
interface EmbeddingConfig {
  modelName: "sentence-transformers/stsb-xlm-r-multilingual";
  dimension: 768;
  batchSize: 32;
  maxTokens: 512;
}
```

### 6.3 ChromaDB設定

```typescript
interface ChromaDBConfig {
  path: string; // データ保存パス（環境変数から取得）
  collectionName: string; // コレクション名（環境変数から取得）
  embeddingFunction: string; // 埋め込み関数の識別子
  persistDirectory: string; // 永続化ディレクトリ（環境変数から取得）
  anonymizedTelemetry: boolean; // 匿名テレメトリ（環境変数から取得）
}
```

**環境変数の読み込み**:

```typescript
import dotenv from "dotenv";
import path from "path";

// .envファイルを読み込み
dotenv.config();

// 環境変数から設定を取得
const config = {
  persistDirectory: process.env.CHROMA_PERSIST_DIRECTORY || "./data/chroma",
  collectionName: process.env.CHROMA_COLLECTION_NAME || "semche_documents",
  embeddingModel:
    process.env.EMBEDDING_MODEL ||
    "sentence-transformers/stsb-xlm-r-multilingual",
  embeddingDimension: parseInt(process.env.EMBEDDING_DIMENSION || "768"),
  hnswSpace: process.env.CHROMA_HNSW_SPACE || "cosine",
  hnswConstructionEf: parseInt(
    process.env.CHROMA_HNSW_CONSTRUCTION_EF || "100"
  ),
  hnswM: parseInt(process.env.CHROMA_HNSW_M || "16"),
  anonymizedTelemetry: process.env.CHROMA_ANONYMIZED_TELEMETRY === "true",
};
```

**ChromaDBの初期化例**:

```typescript
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { HuggingFaceTransformersEmbeddings } from "@langchain/community/embeddings/hf_transformers";
import dotenv from "dotenv";

// 環境変数を読み込み
dotenv.config();

const embeddings = new HuggingFaceTransformersEmbeddings({
  modelName: config.embeddingModel,
});

const vectorStore = new Chroma(embeddings, {
  collectionName: config.collectionName,
  persistDirectory: config.persistDirectory,
  collectionMetadata: {
    "hnsw:space": config.hnswSpace,
    "hnsw:construction_ef": config.hnswConstructionEf,
    "hnsw:M": config.hnswM,
  },
});
```

### 6.4 設定の検証

```typescript
function validateConfig(): void {
  // 必須パスの存在確認と作成
  const persistDir = path.resolve(config.persistDirectory);

  if (!fs.existsSync(persistDir)) {
    console.log(`Creating persist directory: ${persistDir}`);
    fs.mkdirSync(persistDir, { recursive: true });
  }

  // 設定値の検証
  if (config.embeddingDimension <= 0) {
    throw new Error("Invalid EMBEDDING_DIMENSION");
  }

  if (!["cosine", "l2", "ip"].includes(config.hnswSpace)) {
    throw new Error("Invalid CHROMA_HNSW_SPACE");
  }

  console.log("Configuration validated successfully");
  console.log(`Persist directory: ${persistDir}`);
  console.log(`Collection name: ${config.collectionName}`);
}
```

## 7. MCP API仕様

### 7.1 MCPツール定義

#### 7.1.1 indexDocuments ツール

```typescript
{
  name: "indexDocuments",
  description: "ドキュメントをベクトルストアにインデックス化します（upsert動作：既存の場合は更新、新規の場合は追加）",
  inputSchema: {
    type: "object",
    properties: {
      documents: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id: {
              type: "string",
              description: "ドキュメントID（通常はファイルパス）。既存の場合は更新される"
            },
            content: { type: "string", description: "ドキュメントの内容" },
            metadata: {
              type: "object",
              description: "ドキュメントのメタデータ",
              properties: {
                source: { type: "string" },
                filePath: { type: "string" },
                language: { type: "string" },
                timestamp: { type: "string" },
                lastModified: { type: "string" }
              }
            }
          },
          required: ["content"]
        },
        description: "追加するドキュメントの配列"
      },
      chunkSize: {
        type: "number",
        description: "チャンクサイズ（デフォルト: 1000）",
        default: 1000
      },
      chunkOverlap: {
        type: "number",
        description: "チャンクオーバーラップ（デフォルト: 200）",
        default: 200
      },
      upsert: {
        type: "boolean",
        description: "true: 既存ドキュメントを更新、false: 常に新規追加（デフォルト: true）",
        default: true
      }
    },
    required: ["documents"]
  }
}
```

**動作仕様**:

1. **upsert=true（デフォルト）の場合**:
   - ドキュメントに`id`または`metadata.filePath`が指定されている場合、既存のドキュメントを検索
   - 既存のドキュメントが見つかった場合:
     - 古いチャンクを全て削除
     - 新しい内容でチャンク分割して再追加
     - メタデータの`lastModified`を更新
   - 見つからなかった場合:
     - 新規ドキュメントとして追加

2. **upsert=false の場合**:
   - 常に新規ドキュメントとして追加（重複を許可）

**実装例**:

```typescript
async function handleIndexDocuments(args: any) {
  const {
    documents,
    chunkSize = 1000,
    chunkOverlap = 200,
    upsert = true,
  } = args;
  const results = [];

  for (const doc of documents) {
    const docId = doc.id || doc.metadata?.filePath;

    if (upsert && docId) {
      // 既存ドキュメントを検索
      const existing = await vectorStore.similaritySearch("", 1, {
        filter: { filePath: docId },
      });

      if (existing.length > 0) {
        // 既存のチャンクを削除
        await vectorStore.delete({
          filter: { filePath: docId },
        });
        console.error(`[Semche] Updating existing document: ${docId}`);
      }
    }

    // ドキュメントを追加
    const textSplitter = new RecursiveCharacterTextSplitter({
      chunkSize,
      chunkOverlap,
    });

    const chunks = await textSplitter.splitText(doc.content);

    await vectorStore.addDocuments(
      chunks.map((chunk, i) => ({
        pageContent: chunk,
        metadata: {
          ...doc.metadata,
          filePath: docId,
          chunkIndex: i,
          totalChunks: chunks.length,
          lastModified: new Date().toISOString(),
        },
      }))
    );

    results.push({
      id: docId,
      chunks: chunks.length,
      action: existing.length > 0 ? "updated" : "added",
    });
  }

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({ success: true, results }),
      },
    ],
  };
}
```

**レスポンス例**:

```json
{
  "success": true,
  "results": [
    {
      "id": "src/components/Button.tsx",
      "chunks": 5,
      "action": "updated"
    },
    {
      "id": "src/utils/helper.ts",
      "chunks": 3,
      "action": "added"
    }
  ]
}
```

#### 7.1.2 search ツール

```typescript
{
  name: "search",
  description: "セマンティック検索を実行します",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "検索クエリ"
      },
      k: {
        type: "number",
        description: "取得する結果数（デフォルト: 10）",
        default: 10
      },
      filter: {
        type: "object",
        description: "メタデータフィルタ"
      },
      scoreThreshold: {
        type: "number",
        description: "最小スコア閾値",
        default: 0.0
      }
    },
    required: ["query"]
  }
}
```

#### 7.1.3 deleteDocuments ツール

```typescript
{
  name: "deleteDocuments",
  description: "ドキュメントを削除します",
  inputSchema: {
    type: "object",
    properties: {
      ids: {
        type: "array",
        items: { type: "string" },
        description: "削除するドキュメントIDの配列"
      },
      filter: {
        type: "object",
        description: "削除対象のメタデータフィルタ"
      }
    }
  }
}
```

#### 7.1.4 getCollectionInfo ツール

```typescript
{
  name: "getCollectionInfo",
  description: "コレクション情報を取得します",
  inputSchema: {
    type: "object",
    properties: {}
  }
}
```

### 7.2 MCPリソース定義

#### 7.2.1 collection://stats

```typescript
{
  uri: "collection://stats",
  name: "Collection Statistics",
  description: "コレクションの統計情報",
  mimeType: "application/json"
}
```

**レスポンス例**:

```json
{
  "documentCount": 1234,
  "totalChunks": 5678,
  "collectionName": "semche_documents",
  "embeddingDimension": 768,
  "lastUpdated": "2025-11-02T10:30:00Z"
}
```

#### 7.2.2 collection://documents

```typescript
{
  uri: "collection://documents",
  name: "Documents List",
  description: "コレクション内のドキュメント一覧",
  mimeType: "application/json"
}
```

### 7.3 MCPプロンプト定義

#### 7.3.1 semantic-search プロンプト

```typescript
{
  name: "semantic-search",
  description: "セマンティック検索を実行するためのプロンプトテンプレート",
  arguments: [
    {
      name: "query",
      description: "検索クエリ",
      required: true
    },
    {
      name: "context",
      description: "追加のコンテキスト情報",
      required: false
    }
  ]
}
```

## 8. 従来のAPI仕様（後方互換性）

### 8.1 インデックス作成

```typescript
async function createIndex(
  documents: Document[],
  config: IndexConfig
): Promise<IndexResult>;
```

**パラメータ**:

- `documents`: インデックス化するドキュメントの配列
- `config`: インデックス設定

**戻り値**:

- インデックス作成結果

### 8.2 ドキュメントのインデックス化

```typescript
async function indexDocuments(
  indexId: string,
  documents: Document[]
): Promise<IndexResult>;
```

### 7.3 類似度検索

```typescript
async function search(
  indexId: string,
  query: string,
  options: SearchOptions
): Promise<SearchResponse>;
```

**パラメータ**:

- `indexId`: 検索対象のインデックスID
- `query`: 検索クエリ
- `options`: 検索オプション
  - `k`: 取得する結果数（デフォルト: 10）
  - `filter`: メタデータフィルタ
  - `scoreThreshold`: 最小スコア閾値

### 7.4 ドキュメント削除

```typescript
async function deleteDocuments(
  indexId: string,
  documentIds: string[]
): Promise<DeleteResult>;
```

## 9. 設定仕様

### 9.1 Cursor MCP設定

**設定ファイルの場所**:

- macOS/Linux: `~/.cursor/mcp_settings.json`
- Windows: `%APPDATA%\Cursor\User\mcp_settings.json`

**設定例**:

```json
{
  "mcpServers": {
    "semche": {
      "command": "node",
      "args": ["/absolute/path/to/semche/dist/index.js"],
      "env": {
        "CHROMA_PERSIST_DIRECTORY": "/absolute/path/to/data/chroma",
        "CHROMA_COLLECTION_NAME": "semche_documents",
        "EMBEDDING_MODEL": "sentence-transformers/stsb-xlm-r-multilingual"
      }
    }
  }
}
```

**プロジェクトごとの設定**:

```json
{
  "mcpServers": {
    "semche": {
      "command": "node",
      "args": ["${workspaceFolder}/node_modules/.bin/semche"],
      "env": {
        "CHROMA_PERSIST_DIRECTORY": "${workspaceFolder}/.semche/data",
        "CHROMA_COLLECTION_NAME": "${workspaceFolderBasename}"
      }
    }
  }
}
```

### 9.2 ワークスペース統合

**Cursor設定ファイル (.vscode/settings.json)**:

```json
{
  "mcp.servers": {
    "semche": {
      "enabled": true,
      "autoIndex": true,
      "indexPatterns": [
        "**/*.ts",
        "**/*.js",
        "**/*.tsx",
        "**/*.jsx",
        "**/*.py",
        "**/*.md"
      ],
      "excludePatterns": [
        "**/node_modules/**",
        "**/dist/**",
        "**/.git/**"
      ]
    }
  }
}
  }
}
```

### 9.3 環境変数設定

```typescript
interface ChunkConfig {
  chunkSize: number; // チャンクサイズ（デフォルト: 1000文字）
  chunkOverlap: number; // オーバーラップサイズ（デフォルト: 200文字）
  separator: string; // 分割セパレータ（デフォルト: "\n"）
}
```

### 9.4 検索設定

```typescript
interface SearchConfig {
  defaultK: number; // デフォルト取得件数（デフォルト: 10）
  maxK: number; // 最大取得件数（デフォルト: 100）
  scoreThreshold: number; // デフォルトスコア閾値（デフォルト: 0.0）
  searchType: "similarity" | "mmr"; // 検索タイプ
}
```

### 9.5 ChromaDBストレージ設定

```typescript
interface StorageConfig {
  persistDirectory: string; // 永続化ディレクトリ（.envから読み込み）
  collectionName: string; // コレクション名（.envから読み込み）
  collectionMetadata: {
    "hnsw:space": "cosine" | "l2" | "ip"; // 距離計算方式（.envから読み込み）
    "hnsw:construction_ef": number; // インデックス構築時の探索深度（.envから読み込み）
    "hnsw:M": number; // グラフの接続数（.envから読み込み）
  };
  createCollection: boolean; // コレクション自動作成（デフォルト: true）
}
```

**環境変数から設定を読み込む**:

```typescript
import dotenv from "dotenv";

dotenv.config();

const storageConfig: StorageConfig = {
  persistDirectory: process.env.CHROMA_PERSIST_DIRECTORY || "./data/chroma",
  collectionName: process.env.CHROMA_COLLECTION_NAME || "semche_documents",
  collectionMetadata: {
    "hnsw:space":
      (process.env.CHROMA_HNSW_SPACE as "cosine" | "l2" | "ip") || "cosine",
    "hnsw:construction_ef": parseInt(
      process.env.CHROMA_HNSW_CONSTRUCTION_EF || "100"
    ),
    "hnsw:M": parseInt(process.env.CHROMA_HNSW_M || "16"),
  },
  createCollection: true,
};
```

### 9.6 環境変数の優先順位

1. MCPサーバー起動時の環境変数（claude_desktop_config.jsonから）
2. システム環境変数
3. .envファイルの値
4. デフォルト値（ハードコード）

### 9.7 MCPサーバー実装例

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { HuggingFaceTransformersEmbeddings } from "@langchain/community/embeddings/hf_transformers";
import dotenv from "dotenv";

dotenv.config();

// MCPサーバーの初期化
const server = new Server(
  {
    name: "semche",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

// ベクトルストアの初期化
const embeddings = new HuggingFaceTransformersEmbeddings({
  modelName:
    process.env.EMBEDDING_MODEL ||
    "sentence-transformers/stsb-xlm-r-multilingual",
});

const vectorStore = new Chroma(embeddings, {
  collectionName: process.env.CHROMA_COLLECTION_NAME || "semche_documents",
  persistDirectory: process.env.CHROMA_PERSIST_DIRECTORY || "./data/chroma",
});

// ツールハンドラーの登録
server.setRequestHandler("tools/list", async () => {
  return {
    tools: [
      {
        name: "indexDocuments",
        description:
          "ドキュメントをベクトルストアにインデックス化します（upsert動作）",
        inputSchema: {
          /* ... */
        },
      },
      {
        name: "search",
        description: "セマンティック検索を実行します",
        inputSchema: {
          /* ... */
        },
      },
      // ... その他のツール
    ],
  };
});

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "indexDocuments":
      return await handleIndexDocuments(args);
    case "search":
      return await handleSearch(args);
    case "deleteDocuments":
      return await handleDeleteDocuments(args);
    case "getCollectionInfo":
      return await handleGetCollectionInfo(args);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// サーバー起動
const transport = new StdioServerTransport();
await server.connect(transport);
```

**設定値の上書き例**:

```typescript
// 実行時に環境変数を上書き
process.env.CHROMA_PERSIST_DIRECTORY = "/custom/path/to/data";

// または起動時にコマンドラインで指定
// CHROMA_PERSIST_DIRECTORY=/custom/path/to/data npm start
```

## 9. パフォーマンス要件

- **インデックス作成**: 1000ドキュメント/分以上
- **検索レスポンス**: 100ms以下（1000ドキュメントまで）
- **同時検索**: 10リクエスト/秒以上

## 10. エラーハンドリング

### 10.1 エラータイプ

```typescript
enum ErrorType {
  INVALID_INPUT = "INVALID_INPUT",
  INDEX_NOT_FOUND = "INDEX_NOT_FOUND",
  EMBEDDING_ERROR = "EMBEDDING_ERROR",
  STORAGE_ERROR = "STORAGE_ERROR",
  SEARCH_ERROR = "SEARCH_ERROR",
  CONFIG_ERROR = "CONFIG_ERROR",
  ENV_ERROR = "ENV_ERROR",
}

interface SemcheError {
  type: ErrorType;
  message: string;
  details?: any;
}
```

### 10.2 環境変数エラーの例

```typescript
// 環境変数の検証
function validateEnvironment(): void {
  const required = ["CHROMA_PERSIST_DIRECTORY", "CHROMA_COLLECTION_NAME"];

  for (const key of required) {
    if (!process.env[key]) {
      throw {
        type: ErrorType.ENV_ERROR,
        message: `Missing required environment variable: ${key}`,
        details: { variable: key },
      } as SemcheError;
    }
  }

  // パスの検証
  const persistDir = process.env.CHROMA_PERSIST_DIRECTORY;
  if (persistDir && !path.isAbsolute(persistDir)) {
    // 相対パスの場合は絶対パスに変換
    process.env.CHROMA_PERSIST_DIRECTORY = path.resolve(persistDir);
  }
}
```

## 11. セキュリティ要件

- **環境変数管理**:
  - .envファイルを.gitignoreに追加
  - .env.exampleをテンプレートとして提供
  - 本番環境では環境変数を直接設定
- **APIキー**: 安全な管理と暗号化
- **アクセス制御**: ドキュメントアクセス権限の制御
- **入力検証**: 検索クエリのサニタイズ
- **レート制限**: API呼び出しの制限実装
- **データ暗号化**: ローカルデータの暗号化（オプション）
- **ファイル権限**: データディレクトリのアクセス権限設定（700または750）
- **バックアップ**: 定期的なバックアップとリストア機能

### 11.1 .gitignore設定例

```gitignore
# 環境変数ファイル
.env
.env.local
.env.*.local

# データディレクトリ
data/
*.sqlite3

# ログファイル
logs/
*.log
```

### 11.2 .env.example

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
```

## 12. 拡張性

### 12.1 将来的な拡張

- 複数の埋め込みモデルのサポート
- ハイブリッド検索（キーワード + ベクトル）
- クエリ拡張機能
- 検索結果のリランキング
- 分散処理対応

## 13. 開発環境

### 13.1 必要なパッケージ

```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0",
    "langchain": "^0.1.0",
    "@langchain/community": "^0.0.1",
    "chromadb": "^1.7.0",
    "@xenova/transformers": "^2.10.0",
    "dotenv": "^16.3.0",
    "typescript": "^5.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/dotenv": "^8.2.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts",
    "inspector": "npx @modelcontextprotocol/inspector dist/index.js"
  }
}
```

### 13.2 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### 13.3 開発ツール

- Node.js 18以上
- TypeScript 5.0以上
- MCP Inspector（デバッグ用）
- ESLint
- Prettier
- Jest（テスト用）

### 13.4 MCPサーバーのデバッグ

**MCP Inspectorの使用**:

```bash
# ビルド
npm run build

# MCP Inspectorで起動
npx @modelcontextprotocol/inspector dist/index.js
```

**ログ出力**:

```typescript
// stderr にログを出力（stdioトランスポート使用時）
console.error("[Semche] Initializing vector store...");
console.error(`[Semche] Collection: ${collectionName}`);
```

## 14. テスト仕様

### 14.1 ユニットテスト

- 埋め込み生成のテスト
- チャンク分割のテスト
- 検索ロジックのテスト
- MCPツールハンドラーのテスト
- 環境変数読み込みのテスト

### 14.2 統合テスト

- エンドツーエンドの検索フロー
- 大量データでのパフォーマンステスト
- エラーケースのテスト
- MCPプロトコル通信のテスト

### 14.3 MCPサーバーテスト

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

describe("Semche MCP Server", () => {
  let client: Client;

  beforeAll(async () => {
    const transport = new StdioClientTransport({
      command: "node",
      args: ["dist/index.js"],
    });

    client = new Client(
      {
        name: "test-client",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );

    await client.connect(transport);
  });

  test("should list available tools", async () => {
    const response = await client.request(
      {
        method: "tools/list",
      },
      {}
    );

    expect(response.tools).toContainEqual(
      expect.objectContaining({ name: "indexDocuments" })
    );
    expect(response.tools).toContainEqual(
      expect.objectContaining({ name: "search" })
    );
  });

  test("should index documents", async () => {
    const response = await client.request(
      {
        method: "tools/call",
        params: {
          name: "indexDocuments",
          arguments: {
            documents: [
              { content: "テストドキュメント", metadata: { source: "test" } },
            ],
          },
        },
      },
      {}
    );

    expect(response.isError).toBe(false);
  });

  test("should perform search", async () => {
    const response = await client.request(
      {
        method: "tools/call",
        params: {
          name: "search",
          arguments: {
            query: "テスト",
            k: 5,
          },
        },
      },
      {}
    );

    expect(response.content).toBeDefined();
  });

  afterAll(async () => {
    await client.close();
  });
});
```

## 15. デプロイメント

### 15.1 Cursorへのインストール

#### 1. プロジェクトのビルド

```bash
# プロジェクトのクローンまたは作成
cd /path/to/semche

# 依存関係のインストール
npm install

# TypeScriptのビルド
npm run build
```

#### 2. Cursor MCP設定

**設定ファイルを開く**:

macOS/Linux:

```bash
code ~/.cursor/mcp_settings.json
```

Windows:

```powershell
code $env:APPDATA\Cursor\User\mcp_settings.json
```

#### 3. Semche MCPサーバーを登録

```json
{
  "mcpServers": {
    "semche": {
      "command": "node",
      "args": ["/absolute/path/to/semche/dist/index.js"],
      "env": {
        "CHROMA_PERSIST_DIRECTORY": "/absolute/path/to/.semche/data",
        "CHROMA_COLLECTION_NAME": "my_project",
        "EMBEDDING_MODEL": "sentence-transformers/stsb-xlm-r-multilingual"
      }
    }
  }
}
```

#### 4. Cursorを再起動

Cursorを完全に終了してから再起動します。

#### 5. 動作確認

Cursor内でAIチャットを開き、以下を試します:

```
# プロジェクトのインデックス化
"プロジェクトのすべてのTypeScriptファイルをインデックス化してください"

# セマンティック検索
"認証に関連するコードを探してください"

# コード説明
"このプロジェクトのベクトル検索の実装を説明してください"
```

### 15.2 プロジェクトごとの設定

各プロジェクトに個別のインデックスを持つ設定:

**.cursor/mcp.json** (プロジェクトルート):

```json
{
  "semche": {
    "env": {
      "CHROMA_PERSIST_DIRECTORY": "${workspaceFolder}/.semche/data",
      "CHROMA_COLLECTION_NAME": "${workspaceFolderBasename}"
    }
  }
}
```

### 15.3 自動インデックス化設定

**package.json scripts**:

```json
{
  "scripts": {
    "semche:index": "node scripts/index-project.js",
    "semche:watch": "node scripts/watch-and-index.js",
    "postinstall": "npm run semche:index"
  }
}
```

**index-project.js**:

```javascript
// プロジェクトファイルを自動的にインデックス化
const { execSync } = require("child_process");
const glob = require("glob");

const files = glob.sync("src/**/*.{ts,js,tsx,jsx}", {
  ignore: ["**/node_modules/**", "**/dist/**"],
});

console.log(`Indexing ${files.length} files...`);
// MCPサーバーを呼び出してインデックス化
```

### 15.4 スタンドアロンサーバーとして

```bash
# 本番モード
NODE_ENV=production node dist/index.js

# または環境変数を指定
CHROMA_PERSIST_DIRECTORY=/data/chroma node dist/index.js
```

### 15.5 Docker対応（開発環境用）

**Dockerfile**:

```dockerfile
FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY dist ./dist
COPY .env.example .env

CMD ["node", "dist/index.js"]
```

**docker-compose.yml**:

```yaml
version: "3.8"
services:
  semche:
    build: .
    volumes:
      - ./data:/app/data
      - ${WORKSPACE_FOLDER}:/workspace:ro
    environment:
      - CHROMA_PERSIST_DIRECTORY=/app/data/chroma
      - CHROMA_COLLECTION_NAME=semche_documents
    restart: unless-stopped
```

### 15.6 デプロイ環境

- **Cursor IDE統合**（推奨）
- Docker対応（開発環境用）
- CI/CD パイプライン
- モニタリング・ロギング

### 15.7 モニタリング指標

- MCPツール呼び出し回数（特にsearch）
- 検索レスポンスタイム
- インデックス作成時間
- エラー率
- リソース使用率
- ChromaDBストレージサイズ
- Cursorワークスペースごとのインデックス数

## 16. ドキュメント

### 16.1 必須ドキュメント

- **Cursor設定ガイド**: Cursorへのインストール手順
- **MCP APIリファレンス**: ツール、リソース、プロンプトの詳細
- **使用例・チュートリアル**: Cursorでの基本的な使い方
- **トラブルシューティングガイド**: よくある問題と解決方法
- **パフォーマンスチューニングガイド**: 大規模プロジェクトでの最適化

### 16.2 Cursorでの使用例

#### シナリオ1: プロジェクトのインデックス化（初回）

```
ユーザー（Cursorチャット）:
"このプロジェクトのすべてのTypeScriptファイルをインデックス化してください"

Cursor AI:
semcheのindexDocumentsツールを使用します。
[src/**/*.tsファイルを読み込み、インデックス化を実行]

結果:
✅ 142個のファイルをインデックス化しました（全て新規追加）
- src/: 95ファイル (added)
- tests/: 47ファイル (added)
```

#### シナリオ2: ファイル変更後の再インデックス化（自動更新）

```
ユーザー:
[Button.tsxファイルを編集して保存]
"変更したファイルを再インデックス化してください"

Cursor AI:
semcheのindexDocumentsツールを使用します（upsert動作）。
[Button.tsxの既存インデックスを検出 → 削除 → 新しい内容で再追加]

結果:
✅ 1個のファイルを更新しました
- src/components/Button.tsx (updated)
  - 以前: 4チャンク
  - 更新後: 5チャンク
  - 最終更新: 2025-11-02 10:45:32
```

#### シナリオ3: 複数ファイルの一括更新

```
ユーザー:
"変更した3つのファイルを再インデックス化してください"

Cursor AI:
semcheのindexDocumentsツールで一括処理します。

結果:
✅ 3個のファイルを処理しました
- src/api/auth.ts (updated) - 6チャンク
- src/components/Login.tsx (updated) - 4チャンク
- src/utils/validator.ts (added) - 2チャンク（新規ファイル）
```

- tests/: 47ファイル

```

#### シナリオ2: セマンティックコード検索

```

ユーザー:
"データベース接続を管理しているコードを見つけてください"

Cursor AI:
semcheのsearchツールで検索します。
[search("database connection management", k=5)]

結果:

1. src/db/connection.ts (スコア: 0.92)
2. src/config/database.ts (スコア: 0.87)
3. src/utils/pool.ts (スコア: 0.81)
   ...

```

#### シナリオ3: 類似コードの検索

```

ユーザー:
"このコンポーネントと似たパターンを持つコードを探してください"
[コードブロックを選択]

Cursor AI:
選択されたコードと類似したパターンを検索します。
[similar-codeプロンプトを使用して検索]

結果:
類似したReactコンポーネントを3つ見つけました...

```

### 16.3 ベストプラクティス

#### Cursorでの効果的な利用

1. **ドキュメントIDの管理**
   - ファイルパスを`id`または`metadata.filePath`として使用
   - 一貫したID形式で重複を防止
   - 相対パスの使用を推奨（プロジェクトルートからの相対パス）

2. **upsert機能の活用**
   - デフォルトの`upsert=true`を使用して自動更新
   - ファイル保存時に同じIDで`indexDocuments`を呼び出すだけで更新可能
   - 重複を避けるため、常にファイルパスをIDとして指定

3. **定期的なインデックス更新**
   - ファイル変更後は`indexDocuments`で自動更新（既存の場合は上書き）
   - `.semche/data`をgitignoreに追加
   - Git操作後（pull/merge）は変更ファイルを再インデックス

4. **検索クエリの最適化**
   - 具体的な技術用語を使用
   - 「○○を実装しているコード」など目的を明確に

5. **プロジェクト構造の活用**
   - メタデータフィルタで特定ディレクトリに絞り込み
   - ファイルタイプで検索範囲を制限

6. **パフォーマンス**
   - 大規模プロジェクトでは段階的にインデックス化
   - 不要なファイル（node_modules等）は除外
   - upsertによる差分更新で効率化

7. **重複の回避**
   - `upsert=true`（デフォルト）を使用
   - 明示的に重複を許可したい場合のみ`upsert=false`
   - ファイル移動時は古いパスを削除してから新しいパスで追加

## 17. ライセンス

未定

## 18. 付録

### 18.1 MCPプロトコルバージョン

- MCP SDK: 0.5.0以上
- Protocol Version: 2024-11-05

### 18.2 サポートするMCPクライアント

- **Cursor IDE** (推奨・主要対象)
  - macOS
  - Windows
  - Linux
- Claude Desktop (互換性あり)
- カスタムMCPクライアント実装

### 18.3 Cursor固有の機能

- ワークスペース変数のサポート (`${workspaceFolder}`)
- プロジェクトごとの独立したインデックス
- Cursorのファイルウォッチャーとの統合
- コンテキストメニューからの直接呼び出し

### 18.4 制限事項

- stdio トランスポートのみサポート（初版）
- 単一コレクションのみ対応（プロジェクトごと）
- 同時接続数: 1クライアントまで（stdioの制約）
- バイナリファイルは非対応
- 最大ファイルサイズ: 10MB/ファイル

### 18.5 推奨プロジェクトサイズ

- 小規模: ~1,000ファイル（即座にインデックス化）
- 中規模: 1,000~10,000ファイル（数分でインデックス化）
- 大規模: 10,000+ファイル（段階的インデックス化を推奨）

## 19. 変更履歴

| バージョン | 日付       | 変更内容                             | 担当者 |
| ---------- | ---------- | ------------------------------------ | ------ |
| 1.0.0      | 2025-11-02 | 初版作成（Cursor IDE MCP対応を含む） | -      |
```
