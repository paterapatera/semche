# タスク14: ドキュメントの作成

## 目的

ユーザーと開発者向けの包括的なドキュメントを作成し、システムの使用と保守を容易にする

## 作業内容

### 1. README.mdの作成

```markdown
# Semche - Semantic Code Search MCP Server

Cursor IDE用のベクトル検索MCPサーバー。LangChainとChromaDBを使用した高度なセマンティックコード検索機能を提供します。

## 特徴

- 🔍 **セマンティック検索**: 自然言語でコードベースを検索
- 📚 **多言語サポート**: 多言語埋め込みモデル（sentence-transformers/stsb-xlm-r-multilingual）
- 💾 **ローカルストレージ**: ChromaDBによる永続化
- 🔄 **自動インデックス**: ファイル監視による自動更新（オプション）
- 🎯 **Cursor統合**: MCP経由でCursor IDEとシームレスに連携
- ⚡ **高速検索**: HNSW アルゴリズムによる効率的な類似度検索

## クイックスタート

### 前提条件

- Node.js 20以上
- npm または yarn

### インストール

\`\`\`bash

# リポジトリのクローン

git clone https://github.com/yourusername/semche.git
cd semche

# 依存関係のインストール

npm install

# ビルド

npm run build
\`\`\`

### 設定

\`\`\`bash

# .envファイルの作成

cp .env.example .env

# .envファイルを編集して設定をカスタマイズ

nano .env
\`\`\`

### Cursor IDEでの設定

\`.cursor/mcp.json\` ファイルを作成:

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

## 使い方

### ドキュメントのインデックス

Cursorチャットで:

\`\`\`
このファイルをインデックスして
\`\`\`

または:

\`\`\`
プロジェクト全体をインデックス
\`\`\`

### コードの検索

\`\`\`
ユーザー認証の実装を探して
\`\`\`

\`\`\`
データベース接続のコードを見せて
\`\`\`

### コレクション情報の確認

\`\`\`
ベクトルストアの統計を表示
\`\`\`

または:

\`\`\`
@collection://stats
\`\`\`

## MCPツール

### indexDocuments

ドキュメントをインデックス化（追加・更新）

**引数:**

- \`documents\`: インデックスするドキュメントの配列
- \`upsert\`: 既存ドキュメントを更新するか（デフォルト: true）

### search

セマンティック検索を実行

**引数:**

- \`query\`: 検索クエリ（自然言語）
- \`k\`: 返す結果の数（デフォルト: 5）
- \`filter\`: メタデータフィルター（オプション）

### deleteDocuments

ドキュメントを削除

**引数:**

- \`ids\`: 削除するドキュメントIDの配列
- \`filter\`: フィルターに一致するドキュメントを削除

### getCollectionInfo

コレクション情報を取得

## MCPリソース

- \`collection://stats\`: 統計情報
- \`collection://documents\`: インデックスされたドキュメント一覧
- \`collection://config\`: 現在の設定

## MCPプロンプト

- \`semantic-search\`: セマンティック検索プロンプト
- \`code-explanation\`: コード説明プロンプト
- \`similar-code\`: 類似コード検索プロンプト

## 設定オプション

| 環境変数          | デフォルト                                    | 説明                   |
| ----------------- | --------------------------------------------- | ---------------------- |
| COLLECTION_NAME   | semche-collection                             | コレクション名         |
| PERSIST_DIRECTORY | ./data/chroma                                 | データ保存ディレクトリ |
| EMBEDDING_MODEL   | sentence-transformers/stsb-xlm-r-multilingual | 埋め込みモデル         |
| CHUNK_SIZE        | 1000                                          | チャンクサイズ         |
| CHUNK_OVERLAP     | 200                                           | チャンクオーバーラップ |
| WATCH_ENABLED     | false                                         | ファイル監視の有効化   |

詳細は [.env.example](.env.example) を参照。

## 開発

### テストの実行

\`\`\`bash

# 全テスト

npm run test

# カバレッジ付き

npm run test:coverage

# ウォッチモード

npm run test:watch
\`\`\`

### 開発モード

\`\`\`bash
npm run dev
\`\`\`

## トラブルシューティング

### 埋め込みモデルのダウンロードが遅い

初回起動時にモデル（約400MB）をダウンロードします。インターネット接続を確認してください。

### Cursor IDEで認識されない

1. \`.cursor/mcp.json\` のパスを確認
2. Cursor IDEを再起動
3. MCPサーバーが起動しているか確認

### 検索結果が返らない

1. ドキュメントがインデックスされているか確認
2. \`getCollectionInfo\` でコレクション状態を確認

## ライセンス

MIT

## 貢献

Issue、Pull Requestを歓迎します！

## 関連リンク

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangChain](https://js.langchain.com/)
- [ChromaDB](https://www.trychroma.com/)
- [Cursor IDE](https://cursor.sh/)
```

### 2. API.mdの作成

```markdown
# Semche API Documentation

## Tools

### indexDocuments

ドキュメントをベクトルストアにインデックス化（作成・更新）します。

#### Request

\`\`\`json
{
"tool": "indexDocuments",
"arguments": {
"documents": [
{
"content": "string (required)",
"metadata": {
"filePath": "string",
"language": "string",
"projectName": "string"
},
"id": "string (optional)"
}
],
"upsert": "boolean (default: true)"
}
}
\`\`\`

#### Response

\`\`\`json
{
"success": true,
"indexed": 1,
"updated": 0,
"chunks": 5,
"message": "Successfully indexed 1 new documents (5 chunks total)"
}
\`\`\`

### search

セマンティック検索を実行します。

#### Request

\`\`\`json
{
"tool": "search",
"arguments": {
"query": "string (required)",
"k": "number (default: 5)",
"filter": {
"filePath": "string",
"language": "string"
},
"scoreThreshold": "number (default: 0.0)"
}
}
\`\`\`

#### Response

\`\`\`json
{
"success": true,
"results": [
{
"content": "string",
"metadata": {
"filePath": "string",
"language": "string",
"chunkIndex": 0,
"totalChunks": 3
},
"score": 0.95
}
],
"query": "user authentication",
"resultCount": 5,
"message": "Found 5 relevant document(s)"
}
\`\`\`

### deleteDocuments

ドキュメントをベクトルストアから削除します。

#### Request

\`\`\`json
{
"tool": "deleteDocuments",
"arguments": {
"ids": ["doc-id-1", "doc-id-2"],
// または
"filter": {
"filePath": "/path/to/file.ts"
}
}
}
\`\`\`

#### Response

\`\`\`json
{
"success": true,
"deleted": 2,
"message": "Successfully deleted 2 document(s)"
}
\`\`\`

### getCollectionInfo

コレクションの統計情報を取得します。

#### Request

\`\`\`json
{
"tool": "getCollectionInfo",
"arguments": {}
}
\`\`\`

#### Response

\`\`\`json
{
"success": true,
"info": {
"collectionName": "semche-collection",
"documentCount": 42,
"chunkCount": 287,
"uniqueFiles": 42,
"languages": ["typescript", "javascript", "python"],
"embeddingModel": "sentence-transformers/stsb-xlm-r-multilingual",
"embeddingDimension": 768,
"persistDirectory": "./data/chroma",
"storageSize": "15.3 MB",
"recentDocuments": [...]
}
}
\`\`\`

## Resources

### collection://stats

コレクションの統計情報をMarkdown形式で取得します。

### collection://documents

インデックスされたドキュメントの一覧を取得します。

### collection://config

現在の設定情報を取得します。

## Prompts

### semantic-search

セマンティック検索用のプロンプトテンプレート。

**引数:**

- \`query\`: 検索クエリ
- \`context\`: 追加コンテキスト（オプション）

### code-explanation

コード説明用のプロンプトテンプレート。

**引数:**

- \`functionality\`: 理解したい機能

### similar-code

類似コード検索用のプロンプトテンプレート。

**引数:**

- \`codeOrDescription\`: コードまたは説明
- \`language\`: プログラミング言語（オプション）

## Error Handling

全てのツールは以下の形式でエラーを返します:

\`\`\`json
{
"content": [
{
"type": "text",
"text": "{\\"error\\": \\"Error message\\", \\"code\\": \\"ERROR_CODE\\"}"
}
],
"isError": true
}
\`\`\`

### エラーコード

- \`VECTOR_STORE_ERROR\`: ベクトルストアのエラー
- \`INDEXING_ERROR\`: インデックスのエラー
- \`SEARCH_ERROR\`: 検索のエラー
- \`CONFIGURATION_ERROR\`: 設定のエラー
- \`FILE_WATCHER_ERROR\`: ファイル監視のエラー
```

### 3. ARCHITECTURE.mdの作成

```markdown
# Semche アーキテクチャ

## システム概要

Semcheは、Model Context Protocol (MCP) を使用してCursor IDEと統合されたベクトル検索サーバーです。

## コンポーネント構成

\`\`\`
┌─────────────────┐
│ Cursor IDE │
└────────┬────────┘
│ MCP (stdio)
│
┌────────▼────────┐
│ Semche Server │
│ - Tools │
│ - Resources │
│ - Prompts │
└────────┬────────┘
│
┌────▼─────┬──────────┬──────────┐
│ │ │ │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
│Vector │ │Text │ │File │ │Logger │
│Store │ │Split │ │Watch │ │ │
└───┬───┘ └───────┘ └───────┘ └────────┘
│
┌───▼───────────┐
│ ChromaDB │
│ (SQLite) │
└───────────────┘
\`\`\`

## データフロー

### インデックス作成フロー

1. Cursor IDEからindexDocumentsツール呼び出し
2. テキストをチャンクに分割
3. 埋め込みベクトルを生成
4. ChromaDBに保存

### 検索フロー

1. Cursor IDEからsearchツール呼び出し
2. クエリの埋め込みベクトルを生成
3. ChromaDBで類似度検索
4. 結果をフォーマットして返却

## 技術スタック

- **Runtime**: Node.js 20+
- **Language**: TypeScript 5+
- **MCP SDK**: @modelcontextprotocol/sdk 0.5.0+
- **Vector Store**: ChromaDB 1.7.0+
- **Embeddings**: HuggingFace Transformers
- **Framework**: LangChain

## ディレクトリ構造

\`\`\`
semche/
├── src/
│ ├── index.ts # メインサーバー
│ ├── config.ts # 設定管理
│ ├── tools/ # MCPツール
│ │ ├── indexDocuments.ts
│ │ ├── search.ts
│ │ ├── deleteDocuments.ts
│ │ └── getCollectionInfo.ts
│ ├── resources/ # MCPリソース
│ │ └── index.ts
│ ├── prompts/ # MCPプロンプト
│ │ └── index.ts
│ └── utils/ # ユーティリティ
│ ├── vectorStore.ts
│ ├── textSplitter.ts
│ ├── fileWatcher.ts
│ ├── logger.ts
│ └── errors.ts
├── tests/ # テスト
├── data/ # データ保存
│ └── chroma/
└── logs/ # ログファイル
\`\`\`

## 拡張性

### 新しいツールの追加

1. \`src/tools/\` に新しいツールを作成
2. \`src/index.ts\` でListToolsRequestに追加
3. CallToolRequestハンドラーにケースを追加

### 新しいリソースの追加

1. \`src/resources/index.ts\` に関数を追加
2. ListResourcesRequestに定義を追加
3. ReadResourceRequestハンドラーにケースを追加

## パフォーマンス考慮事項

- **埋め込み生成**: 初回起動時にモデルダウンロード（約400MB）
- **インデックス速度**: チャンクサイズに依存
- **検索速度**: HNSWアルゴリズムにより高速（O(log n)）
- **ストレージ**: SQLiteベースで軽量

## セキュリティ

- ローカル実行のため外部通信なし
- データは全てローカルに保存
- MCPはstdio通信（プロセス間通信）
```

## 完了条件

- [ ] README.mdが作成されている
- [ ] API.mdが作成されている
- [ ] ARCHITECTURE.mdが作成されている
- [ ] AGENTS.mdが作成されている
- [ ] 全てのドキュメントが正確で最新
- [ ] インストール手順が明確
- [ ] 使用例が豊富
- [ ] トラブルシューティングガイドがある

## 動作確認

### ドキュメントの確認

1. README.mdの手順に従ってインストール
2. 各使用例を試す
3. トラブルシューティングが役立つか確認

### リンクの確認

```bash
# マークダウンリンクチェッカー（オプション）
npm install -g markdown-link-check
markdown-link-check README.md
```

## ドキュメントのベストプラクティス

- 実際に動作する例を提供
- スクリーンショットや図を含める（必要に応じて）
- よくある質問への回答を含める
- バージョン情報を明記
- 更新日を記録

## 次のタスク

タスク15: デプロイメントとパッケージング
