# Semche MCP Server - Cursor IDE接続設定

## 本番環境（推奨）

**ファイル:** `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "semche": {
      "command": "node",
      "args": ["/home/pater/semche/dist/index.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

**使用方法:**

1. `npm run build` でビルド
2. Cursor IDEを再起動
3. 設定 > MCP から接続を確認

## 開発環境

**ファイル:** `.cursor/mcp-dev.json`

```json
{
  "mcpServers": {
    "semche-dev": {
      "command": "npm",
      "args": ["run", "dev"],
      "cwd": "/home/pater/semche",
      "env": {
        "NODE_ENV": "development"
      }
    }
  }
}
```

**使用方法:**

1. 開発中にホットリロードで即座に変更を反映
2. `.cursor/mcp-dev.json` を `.cursor/mcp.json` にリネーム
3. Cursor IDEを再起動

## 利用可能なツール

MCPサーバーが提供する4つのツール:

1. **indexDocuments** - ドキュメントのインデックス化
2. **search** - セマンティック検索
3. **deleteDocuments** - ドキュメントの削除
4. **getCollectionInfo** - コレクション情報の取得

## トラブルシューティング

### サーバーが認識されない

1. Cursor IDEを完全に再起動
2. `.cursor/mcp.json` のパスが正しいか確認
3. `npm run build` が成功しているか確認

### 埋め込みモデルのダウンロードエラー

初回起動時に約400MBのモデルをダウンロードします:

- インターネット接続を確認
- ダウンロード先: `~/.cache/huggingface/`
- 必要なディスク容量: 約500MB

### 環境変数エラー

`.env` ファイルが存在し、正しく設定されているか確認:

```bash
cat .env
```
