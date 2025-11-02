# タスク1: プロジェクト初期設定

## 目的

プロジェクトの基本構造とTypeScript環境をセットアップする

## 作業内容

### 1. package.jsonの作成

```bash
npm init -y
```

### 2. 必要な依存パッケージのインストール

#### 本番依存

```bash
npm install @modelcontextprotocol/sdk
npm install langchain
npm install chromadb
npm install @huggingface/transformers
npm install dotenv
```

#### 開発依存

```bash
npm install -D typescript
npm install -D @types/node
npm install -D tsx
npm install -D vite
npm install -D vite-plugin-node
npm install -D vitest
npm install -D @vitest/ui
```

### 3. TypeScript設定 (tsconfig.json)

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
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### 4. Vite設定 (vite.config.ts)

```typescript
import { defineConfig } from "vite";
import { VitePluginNode } from "vite-plugin-node";

export default defineConfig({
  plugins: [
    ...VitePluginNode({
      adapter: "express",
      appPath: "./src/index.ts",
      exportName: "viteNodeApp",
      tsCompiler: "esbuild",
    }),
  ],
  build: {
    target: "node20",
    outDir: "dist",
    lib: {
      entry: "./src/index.ts",
      formats: ["es"],
      fileName: "index",
    },
    rollupOptions: {
      external: [
        "@modelcontextprotocol/sdk",
        "langchain",
        "@langchain/community",
        "@langchain/core",
        "chromadb",
        "@xenova/transformers",
        "dotenv",
        "chokidar",
        "fs",
        "path",
        "crypto",
      ],
    },
    minify: false,
    sourcemap: true,
  },
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  optimizeDeps: {
    include: ["@modelcontextprotocol/sdk", "langchain"],
  },
  test: {
    globals: true,
    environment: "node",
    include: ["tests/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: [
        "node_modules/",
        "tests/",
        "dist/",
        "**/*.d.ts",
        "**/*.config.*",
        "**/mockData/",
      ],
    },
    testTimeout: 30000, // 30秒（埋め込みモデルのロードに時間がかかる場合）
  },
});
```

### 5. package.json scripts設定

```json
{
  "scripts": {
    "build": "vite build",
    "build:tsc": "tsc",
    "start": "node dist/index.js",
    "dev": "vite --host",
    "dev:tsx": "tsx src/index.ts",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage",
    "inspector": "npx @modelcontextprotocol/inspector dist/index.js",
    "watch": "tsc --watch"
  },
  "type": "module"
}
```

### 6. ディレクトリ構造の作成

```bash
mkdir -p src/{tools,resources,prompts,utils}
mkdir -p data/chroma
mkdir -p tests
```

## 完了条件

- [ ] package.jsonが作成され、全依存パッケージがインストールされている
- [ ] tsconfig.jsonが正しく設定されている
- [ ] vite.config.tsが正しく設定されている（テスト設定を含む）
- [ ] npm scriptsが動作する
- [ ] ディレクトリ構造が作成されている
- [ ] `npm run build`でエラーが出ない（空のプロジェクトでもOK）
- [ ] `npm run dev`でVite開発サーバーが起動する
- [ ] `npm run test`でVitestが実行される

## ViteとVitestを使用する利点

- ⚡ **高速な開発**: ホットリロードで即座にコード変更が反映
- 🔨 **最適化されたビルド**: Rollupによる効率的なバンドル
- 🎯 **TypeScriptサポート**: esbuildによる高速なトランスパイル
- 📦 **依存関係の最適化**: 自動的な依存関係のプリバンドル
- 🔧 **柔軟な設定**: カスタマイズ可能なビルドオプション
- 🧪 **統合されたテスト**: ViteとVitestで設定を共有、高速テスト実行
- 🎨 **テストUI**: `npm run test:ui`でブラウザベースのテストインターフェース

## Vite開発モードとテストの使い方

```bash
# 開発モードで起動（ホットリロード有効）
npm run dev

# 従来のtsx方式で起動（Viteなし）
npm run dev:tsx

# TypeScriptコンパイラでビルド
npm run build:tsc

# Viteでビルド（推奨）
npm run build

# テストを実行（1回のみ）
npm run test

# テストをウォッチモードで実行（ファイル変更を監視）
npm run test:watch

# テストUIをブラウザで表示
npm run test:ui

# テストカバレッジを生成
npm run test:coverage
```

## Vitestの特徴

- 🚀 **Jest互換API**: Jestからの移行が容易
- ⚡ **超高速**: Viteのトランスフォームを使用した高速テスト実行
- 🎯 **型安全**: TypeScriptネイティブサポート
- 🔍 **スマートウォッチ**: 変更されたテストのみを再実行
- 📊 **ビルトインカバレッジ**: c8/v8カバレッジプロバイダー内蔵
- 🖥️ **UI**: ブラウザベースの美しいテストインターフェース

## 次のタスク

タスク2: 環境変数とディレクトリ構造の設定
