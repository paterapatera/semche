# vectorStore.ts - コード説明ドキュメント

## 概要

このファイルは、ChromaDBベクトルストアとHuggingFace埋め込みモデルを管理するユーティリティを提供します。シングルトンパターンを使用してベクトルストアインスタンスを管理し、セマンティック検索とドキュメントのインデックス化を可能にします。

## 依存クラス・モジュール一覧

| クラス/モジュール                   | インポート元                                               | ファイルパス                                                                    | 説明                                                       |
| ----------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `Chroma`                            | `@langchain/community/vectorstores/chroma`                 | `node_modules/@langchain/community/dist/vectorstores/chroma.js`                 | ChromaDBベクトルストアのLangChainラッパー                  |
| `HuggingFaceTransformersEmbeddings` | `@langchain/community/embeddings/huggingface_transformers` | `node_modules/@langchain/community/dist/embeddings/huggingface_transformers.js` | HuggingFace Transformersモデルを使用した埋め込み生成クラス |
| `config`                            | `../config.js`                                             | `src/config.ts`                                                                 | アプリケーション設定オブジェクト                           |
| `fs`                                | `fs`                                                       | Node.js組み込み                                                                 | ファイルシステム操作                                       |

## モジュール変数

### vectorStoreInstance

```typescript
let vectorStoreInstance: Chroma | null = null;
```

ベクトルストアのシングルトンインスタンスを保持するモジュールレベルの変数です。

**目的:**

- アプリケーション全体で単一のベクトルストアインスタンスを共有
- 重複した初期化を防ぐ
- メモリ使用量を最適化

**状態:**

- `null`: 未初期化
- `Chroma`: 初期化済み

## エクスポートされる関数

### getVectorStore 関数

ベクトルストアのシングルトンインスタンスを取得または作成します。

**シグネチャ:**

```typescript
export async function getVectorStore(): Promise<Chroma>;
```

**戻り値:**

- `Promise<Chroma>`: ChromaDBベクトルストアのインスタンス

**動作フロー:**

```
1. インスタンス存在チェック
   ↓ (存在する場合)
   既存インスタンスを返す
   ↓ (存在しない場合)
2. 初期化開始ログ出力
   ↓
3. データディレクトリの確認・作成
   ↓
4. 埋め込みモデルの初期化
   ↓
5. ChromaDBインスタンスの作成
   ↓
6. インスタンスをキャッシュ
   ↓
7. インスタンスを返す
```

**詳細な処理:**

#### 1. シングルトンチェック

```typescript
if (vectorStoreInstance) {
  return vectorStoreInstance;
}
```

既にインスタンスが存在する場合、再初期化せずに既存のものを返します。これにより：

- 初期化コストの削減
- モデルの重複ロードを防止
- 一貫性のあるデータアクセス

#### 2. データディレクトリの作成

```typescript
if (!fs.existsSync(config.persistDirectory)) {
  console.error(
    `[Semche] Creating persist directory: ${config.persistDirectory}`
  );
  fs.mkdirSync(config.persistDirectory, { recursive: true });
}
```

ChromaDBのデータ永続化ディレクトリが存在しない場合、再帰的に作成します。

**`recursive: true`の効果:**

```
./data/chroma が存在しない場合:
→ ./data を作成
→ ./data/chroma を作成
```

#### 3. 埋め込みモデルの初期化

```typescript
const embeddings = new HuggingFaceTransformersEmbeddings({
  model: config.embeddingModel,
});
```

HuggingFace Transformersの埋め込みモデルを初期化します。

**デフォルト設定（.envから）:**

- モデル: `sentence-transformers/stsb-xlm-r-multilingual`
- 次元数: 768次元ベクトル
- 特徴: 多言語対応、日本語サポート

**初回実行時の挙動:**

- モデルファイル（約400MB）を自動ダウンロード
- ダウンロード先: `~/.cache/huggingface/`
- 2回目以降はキャッシュから高速ロード

#### 4. ChromaDBインスタンスの作成

```typescript
vectorStoreInstance = new Chroma(embeddings, {
  collectionName: config.collectionName,
  url: undefined, // ローカルモード
  collectionMetadata: {
    "hnsw:space": config.hnswSpace,
    "hnsw:construction_ef": config.hnswConstructionEf,
    "hnsw:M": config.hnswM,
  },
});
```

**パラメータ詳細:**

| パラメータ             | 値                                | 説明                           |
| ---------------------- | --------------------------------- | ------------------------------ |
| `collectionName`       | `"semche_documents"` (デフォルト) | ChromaDBコレクション名         |
| `url`                  | `undefined`                       | ローカルモード（サーバー不要） |
| `hnsw:space`           | `"cosine"`                        | 距離計算方法（コサイン類似度） |
| `hnsw:construction_ef` | `100`                             | インデックス構築時の探索幅     |
| `hnsw:M`               | `16`                              | HNSW グラフの接続数            |

**HNSW (Hierarchical Navigable Small World) とは:**

高速な近似最近傍探索アルゴリズムです。

```
通常の線形探索:    O(n) - 全ベクトルを比較
HNSW:             O(log n) - グラフ構造で高速探索
```

**HNSWパラメータの影響:**

| パラメータ        | 値を上げると         | トレードオフ     |
| ----------------- | -------------------- | ---------------- |
| `construction_ef` | 精度向上             | 構築時間増加     |
| `M`               | 精度向上、検索高速化 | メモリ使用量増加 |
| `space=cosine`    | 方向の類似性重視     | 長さは無視       |

**使用例:**

```typescript
// 基本的な使用
const vectorStore = await getVectorStore();

// ドキュメントの追加
await vectorStore.addDocuments([
  { pageContent: "テキスト内容", metadata: { source: "file.txt" } },
]);

// 類似検索
const results = await vectorStore.similaritySearch("検索クエリ", 5);

// 複数回呼び出しても同じインスタンス
const store1 = await getVectorStore();
const store2 = await getVectorStore();
console.log(store1 === store2); // true
```

### closeVectorStore 関数

ベクトルストアインスタンスをクリーンアップします。

**シグネチャ:**

```typescript
export async function closeVectorStore(): Promise<void>;
```

**戻り値:**

- `Promise<void>`: 完了を示すPromise

**動作:**

```typescript
if (vectorStoreInstance) {
  console.error("[Semche] Closing vector store...");
  vectorStoreInstance = null;
}
```

インスタンスを`null`にすることで、ガベージコレクションの対象にします。

**重要な注意:**

- ChromaDBには明示的な`close()`メソッドがありません
- インスタンスをnullにすることでメモリを解放
- 次回`getVectorStore()`呼び出し時は再初期化されます

**使用例:**

```typescript
// アプリケーション終了時
process.on("SIGINT", async () => {
  await closeVectorStore();
  process.exit(0);
});

// テスト後のクリーンアップ
afterAll(async () => {
  await closeVectorStore();
});
```

### getCollectionStats 関数

コレクションの統計情報を取得します。

**シグネチャ:**

```typescript
export async function getCollectionStats(): Promise<{
  documentCount: number;
  collectionName: string;
  embeddingDimension: number;
}>;
```

**戻り値:**

| プロパティ           | 型       | 説明                           |
| -------------------- | -------- | ------------------------------ |
| `documentCount`      | `number` | コレクション内のドキュメント数 |
| `collectionName`     | `string` | コレクション名                 |
| `embeddingDimension` | `number` | 埋め込みベクトルの次元数       |

**現在の実装状況:**

```typescript
return {
  documentCount: 0, // TODO: 実装が必要
  collectionName: config.collectionName,
  embeddingDimension: config.embeddingDimension,
};
```

⚠️ **注意:** `documentCount`は現在未実装（常に0を返す）

**実装が必要な理由:**

LangChainの`Chroma`ラッパーには直接ドキュメント数を取得するメソッドがありません。実装するには：

1. **ChromaクライアントAPIを直接使用:**

```typescript
import { ChromaClient } from "chromadb";

const client = new ChromaClient();
const collection = await client.getCollection({
  name: config.collectionName,
});
const count = await collection.count();
```

2. **内部状態の管理:**

```typescript
let documentCount = 0;

export async function addDocument(doc: Document) {
  await vectorStore.addDocuments([doc]);
  documentCount++;
}
```

**使用例:**

```typescript
// コレクション情報の取得
const stats = await getCollectionStats();
console.log(`コレクション: ${stats.collectionName}`);
console.log(`ドキュメント数: ${stats.documentCount}`);
console.log(`ベクトル次元: ${stats.embeddingDimension}`);

// MCPリソースとして公開
server.setRequestHandler(GetResourceRequest, async () => ({
  contents: [
    {
      uri: "semche://stats",
      text: JSON.stringify(await getCollectionStats(), null, 2),
    },
  ],
}));
```

## 使用箇所

このベクトルストアモジュールは以下のファイルで使用されます：

| ファイルパス                          | 用途                         |
| ------------------------------------- | ---------------------------- |
| `src/index.ts`                        | サーバー起動時の初期化       |
| `src/tools/index.ts`（予定）          | ドキュメントのインデックス化 |
| `src/tools/search.ts`（予定）         | セマンティック検索の実行     |
| `src/tools/delete.ts`（予定）         | ドキュメントの削除           |
| `src/resources/collection.ts`（予定） | コレクション情報の取得       |
| `tests/vectorStore.test.ts`           | ユニットテスト               |

## 設計パターンと原則

### 1. シングルトンパターン

**目的:**

- アプリケーション全体で単一のベクトルストアインスタンスを保証
- リソースの効率的な利用
- 状態の一貫性

**実装:**

```typescript
let vectorStoreInstance: Chroma | null = null;

export async function getVectorStore(): Promise<Chroma> {
  if (vectorStoreInstance) {
    return vectorStoreInstance; // 既存インスタンスを返す
  }
  // 初期化処理...
  return vectorStoreInstance;
}
```

### 2. 遅延初期化（Lazy Initialization）

ベクトルストアは最初に`getVectorStore()`が呼ばれたときに初期化されます。

**利点:**

- 起動時間の短縮
- 不要な場合はリソースを消費しない
- テストでのモック化が容易

### 3. 関心の分離

各関数は明確な責任を持ちます：

- `getVectorStore()`: 取得・初期化
- `closeVectorStore()`: クリーンアップ
- `getCollectionStats()`: 情報取得

## 技術的な詳細

### ChromaDB とは

ChromaDBは埋め込みベクトル用のオープンソースデータベースです。

**特徴:**

- ローカル実行可能（サーバー不要）
- 自動永続化
- HNSW インデックスによる高速検索
- メタデータフィルタリング対応

**データ構造:**

```
Collection
├── Documents (テキスト)
├── Embeddings (ベクトル)
├── Metadata (メタ情報)
└── IDs (一意識別子)
```

### 埋め込みモデル

**使用モデル:** `sentence-transformers/stsb-xlm-r-multilingual`

**特徴:**

- 多言語対応（日本語、英語など50言語以上）
- 768次元のベクトル出力
- セマンティック類似度に最適化
- 文・段落レベルの埋め込みに適している

**ベクトル化の例:**

```typescript
入力: "猫は可愛い動物です"
出力: [0.123, -0.456, 0.789, ... ] (768次元)

入力: "犬も可愛いペットです"
出力: [0.134, -0.443, 0.801, ... ] (768次元)

コサイン類似度: 0.89 (高い類似性)
```

### コサイン類似度

ベクトル間の類似度を測定する方法です。

```
cosine_similarity = (A · B) / (||A|| × ||B||)

値の範囲: -1 ≤ similarity ≤ 1
  1.0:  完全に同じ方向
  0.0:  直交（無関係）
 -1.0:  完全に反対方向
```

**セマンティック検索での利用:**

```typescript
クエリ: "プログラミング言語"
↓ 埋め込み化
ベクトルA: [0.1, 0.5, ...]

ドキュメント1: "TypeScriptは型安全な言語です"
ベクトルB: [0.12, 0.48, ...]
類似度: 0.92 ← 高い類似性

ドキュメント2: "昨日の天気は晴れでした"
ベクトルC: [0.01, 0.02, ...]
類似度: 0.15 ← 低い類似性
```

## パフォーマンスとメモリ

### 初回起動時

1. **モデルダウンロード**: 約400MB（初回のみ）
2. **モデルロード**: 5-10秒
3. **ChromaDB初期化**: 1秒未満

### 通常動作時

- **メモリ使用量**: 約500MB-1GB（モデル + インデックス）
- **検索速度**: 数ミリ秒（1000ドキュメントまで）
- **インデックス化**: 1ドキュメントあたり50-100ms

### 最適化のヒント

```typescript
// ✅ 推奨: 一度初期化して再利用
const store = await getVectorStore();
await store.addDocuments(docs1);
await store.addDocuments(docs2);

// ❌ 非推奨: 毎回初期化
for (const doc of docs) {
  const store = await getVectorStore(); // シングルトンなので問題ないが無駄
  await store.addDocuments([doc]);
}
```

## エラーハンドリング

### 潜在的なエラー

1. **ディレクトリ作成失敗:**

```typescript
// 権限エラー、ディスク容量不足など
fs.mkdirSync(config.persistDirectory, { recursive: true });
```

2. **モデルダウンロード失敗:**

```typescript
// ネットワークエラー、ディスク容量不足
new HuggingFaceTransformersEmbeddings({ model: ... });
```

3. **ChromaDB初期化失敗:**

```typescript
// ディレクトリアクセス権限、ファイル破損
new Chroma(embeddings, { ... });
```

### 推奨される改善

```typescript
export async function getVectorStore(): Promise<Chroma> {
  try {
    if (vectorStoreInstance) {
      return vectorStoreInstance;
    }

    // ... 初期化処理

    return vectorStoreInstance;
  } catch (error) {
    console.error("[Semche] Failed to initialize vector store:", error);
    throw new Error(`Vector store initialization failed: ${error.message}`);
  }
}
```

## テスト戦略

### ユニットテスト

```typescript
describe("VectorStore", () => {
  afterAll(async () => {
    await closeVectorStore();
  });

  test("should initialize vector store", async () => {
    const store = await getVectorStore();
    expect(store).toBeDefined();
  });

  test("should return same instance (singleton)", async () => {
    const store1 = await getVectorStore();
    const store2 = await getVectorStore();
    expect(store1).toBe(store2);
  });
});
```

### 統合テスト

```typescript
test("should add and search documents", async () => {
  const store = await getVectorStore();

  await store.addDocuments([
    { pageContent: "TypeScript", metadata: { id: "1" } },
  ]);

  const results = await store.similaritySearch("プログラミング", 1);
  expect(results.length).toBeGreaterThan(0);
});
```

## まとめ

このベクトルストアモジュールは、Semche MCPサーバーのコア機能を提供します：

- ✅ **シングルトン管理**: 効率的なリソース利用
- ✅ **自動初期化**: ディレクトリ作成、モデルロード
- ✅ **高速検索**: HNSWアルゴリズムによる近似最近傍探索
- ✅ **多言語対応**: 日本語を含む50以上の言語
- ✅ **永続化**: ローカルディスクへの自動保存

このモジュールを基盤として、セマンティック検索、ドキュメント管理、知識ベース機能が構築されます。
