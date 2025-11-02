# タスク15: デプロイメントとパッケージング

## 目的

本番環境へのデプロイメントとパッケージング設定を完成させ、ユーザーが簡単にインストール・使用できるようにする

## 作業内容

### 1. package.jsonの最終調整

```json
{
  "name": "semche",
  "version": "1.0.0",
  "description": "Semantic code search MCP server for Cursor IDE using LangChain and ChromaDB",
  "main": "dist/index.js",
  "type": "module",
  "bin": {
    "semche": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/index.ts",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:unit": "jest --testPathPattern=tests/.*\\.test\\.ts --testPathIgnorePatterns=integration",
    "test:integration": "jest --testPathPattern=tests/integration",
    "test:performance": "jest --testPathPattern=tests/performance",
    "watch": "tsc --watch",
    "clean": "rm -rf dist coverage",
    "prepublishOnly": "npm run clean && npm run build && npm run test",
    "postinstall": "node scripts/postinstall.js"
  },
  "keywords": [
    "mcp",
    "model-context-protocol",
    "cursor",
    "vector-search",
    "semantic-search",
    "langchain",
    "chromadb",
    "code-search",
    "embeddings"
  ],
  "author": "Your Name <your.email@example.com>",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourusername/semche.git"
  },
  "bugs": {
    "url": "https://github.com/yourusername/semche/issues"
  },
  "homepage": "https://github.com/yourusername/semche#readme",
  "engines": {
    "node": ">=20.0.0",
    "npm": ">=9.0.0"
  },
  "dependencies": {
    "@langchain/community": "^0.0.20",
    "@langchain/core": "^0.1.10",
    "@modelcontextprotocol/sdk": "^0.5.0",
    "chokidar": "^3.5.3",
    "chromadb": "^1.7.0",
    "dotenv": "^16.3.0",
    "langchain": "^0.1.0"
  },
  "devDependencies": {
    "@types/jest": "^29.5.0",
    "@types/node": "^20.0.0",
    "jest": "^29.5.0",
    "ts-jest": "^29.1.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0"
  }
}
```

### 2. インストール後スクリプトの作成

```javascript
// scripts/postinstall.js
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log("🚀 Setting up Semche...\n");

// データディレクトリの作成
const dataDir = path.join(__dirname, "..", "data", "chroma");
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
  console.log("✅ Created data directory:", dataDir);
}

// ログディレクトリの作成
const logsDir = path.join(__dirname, "..", "logs");
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
  console.log("✅ Created logs directory:", logsDir);
}

// .envファイルがなければ.env.exampleをコピー
const envPath = path.join(__dirname, "..", ".env");
const envExamplePath = path.join(__dirname, "..", ".env.example");

if (!fs.existsSync(envPath) && fs.existsSync(envExamplePath)) {
  fs.copyFileSync(envExamplePath, envPath);
  console.log("✅ Created .env file from .env.example");
  console.log("⚠️  Please configure your .env file before running Semche");
}

console.log("\n📚 Next steps:");
console.log("1. Configure .env file");
console.log("2. Setup Cursor IDE integration (.cursor/mcp.json)");
console.log("3. Run: npm start");
console.log("\nFor more information, see README.md\n");
```

### 3. Dockerfileの作成（オプション）

```dockerfile
# Dockerfile
FROM node:20-alpine

# 作業ディレクトリの設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm ci --only=production

# ソースコードをコピー
COPY . .

# ビルド
RUN npm run build

# データディレクトリの作成
RUN mkdir -p /app/data/chroma /app/logs

# 環境変数のデフォルト値
ENV NODE_ENV=production \
    COLLECTION_NAME=semche-collection \
    PERSIST_DIRECTORY=/app/data/chroma

# ポート（MCPはstdioなので不要だが、将来の拡張用）
EXPOSE 3000

# 起動コマンド
CMD ["npm", "start"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  semche:
    build: .
    container_name: semche
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

### 4. .npmignoreの作成

```
# .npmignore
# テスト
tests/
*.test.ts
*.spec.ts
coverage/

# 開発ファイル
.env
.env.example
.vscode/
.cursor/

# ビルドファイル（srcのみを除外、distは含める）
src/

# ログとデータ
logs/
data/

# ドキュメント（READMEは除く）
docs/
*.md
!README.md

# CI/CD
.github/
.gitlab-ci.yml

# その他
.DS_Store
*.log
node_modules/
.gitignore
```

### 5. リリースワークフローの作成

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "20"
          registry-url: "https://registry.npmjs.org"

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm run test

      - name: Build
        run: npm run build

      - name: Publish to npm
        run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

### 6. CHANGELOGの作成

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-01

### Added

- Initial release
- MCP server implementation for Cursor IDE
- indexDocuments tool with upsert support
- search tool with semantic search
- deleteDocuments tool
- getCollectionInfo tool
- MCP resources (stats, documents, config)
- MCP prompts (semantic-search, code-explanation, similar-code)
- File watching functionality with chokidar
- ChromaDB local persistence
- Multi-language embedding model support
- Comprehensive error handling and logging
- Full test suite with >70% coverage
- Documentation (README, API, Architecture)

### Security

- All data stored locally
- No external communication
- stdio-based MCP communication

## [Unreleased]

### Planned

- Web interface for standalone usage
- Support for additional embedding models
- Advanced filtering options
- Batch indexing optimization
```

### 7. インストールガイドの作成

```markdown
# INSTALL.md

## インストール方法

### 方法1: npmからインストール（推奨）

\`\`\`bash
npm install -g semche
\`\`\`

### 方法2: ソースからビルド

\`\`\`bash

# リポジトリのクローン

git clone https://github.com/yourusername/semche.git
cd semche

# 依存関係のインストール

npm install

# ビルド

npm run build

# グローバルリンク（オプション）

npm link
\`\`\`

### 方法3: Docker

\`\`\`bash

# Dockerイメージのビルド

docker-compose build

# 起動

docker-compose up -d
\`\`\`

## 設定

### 1. 環境変数の設定

\`\`\`bash
cp .env.example .env
nano .env
\`\`\`

最低限必要な設定:
\`\`\`bash
COLLECTION_NAME=my-project-collection
PERSIST_DIRECTORY=./data/chroma
\`\`\`

### 2. Cursor IDE設定

\`.cursor/mcp.json\` を作成:

\`\`\`json
{
"mcpServers": {
"semche": {
"command": "semche",
"env": {
"NODE_ENV": "production"
}
}
}
}
\`\`\`

または、フルパスで指定:

\`\`\`json
{
"mcpServers": {
"semche": {
"command": "node",
"args": ["/path/to/semche/dist/index.js"]
}
}
}
\`\`\`

### 3. 動作確認

1. Cursor IDEを再起動
2. チャットで「利用可能なツールは？」と質問
3. semcheのツールが表示されることを確認

## トラブルシューティング

### インストールが失敗する

\`\`\`bash

# キャッシュをクリア

npm cache clean --force

# 再インストール

npm install
\`\`\`

### Cursor IDEで認識されない

1. \`.cursor/mcp.json\` のパスを確認
2. Cursor IDEを完全に再起動
3. ログを確認: \`tail -f ./logs/semche.log\`

### 埋め込みモデルのダウンロードが遅い

初回起動時にモデル（約400MB）をダウンロードします。
キャッシュは \`~/.cache/huggingface/\` に保存されます。

## アンインストール

### npm経由でインストールした場合

\`\`\`bash
npm uninstall -g semche
\`\`\`

### ソースからビルドした場合

\`\`\`bash
npm unlink # グローバルリンクを削除
rm -rf semche/ # ディレクトリを削除
\`\`\`

### データの削除

\`\`\`bash
rm -rf ./data/chroma # ベクトルデータ
rm -rf ./logs # ログファイル
\`\`\`
```

## 完了条件

- [ ] package.jsonが本番用に最適化されている
- [ ] postinstall スクリプトが作成されている
- [ ] Dockerfileとdocker-compose.ymlが作成されている
- [ ] .npmignoreが適切に設定されている
- [ ] リリースワークフローが設定されている
- [ ] CHANGELOGが作成されている
- [ ] INSTALL.mdが作成されている
- [ ] 全ての設定ファイルが正しく動作する

## 動作確認

### ローカルでのパッケージテスト

```bash
# パッケージをビルド
npm pack

# 別のディレクトリでインストールテスト
mkdir test-install
cd test-install
npm install ../semche-1.0.0.tgz
```

### Dockerでのテスト

```bash
# イメージをビルド
docker-compose build

# 起動
docker-compose up

# ログを確認
docker-compose logs -f
```

### リリースプロセス

1. バージョンを更新:

   ```bash
   npm version patch  # 1.0.0 -> 1.0.1
   # または
   npm version minor  # 1.0.0 -> 1.1.0
   # または
   npm version major  # 1.0.0 -> 2.0.0
   ```

2. CHANGELOGを更新

3. コミットしてプッシュ:

   ```bash
   git push origin main --tags
   ```

4. GitHub Actionsが自動的にnpmへ公開

## 配布方法

### npm公開

```bash
npm login
npm publish
```

### GitHub Releases

1. GitHubでリリースを作成
2. タグを選択（例: v1.0.0）
3. リリースノートを追加
4. アセットを添付（オプション）

## トラブルシューティング

- npm公開に失敗: NPM_TOKENを確認
- Dockerビルドエラー: Dockerfileのパスを確認
- postinstallエラー: スクリプトの実行権限を確認

## 次のタスク

タスク16: 最終確認とリリース準備
