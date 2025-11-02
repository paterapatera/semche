# タスク16: 最終確認とリリース準備

## 目的

全ての実装を統合し、最終的な動作確認とリリース準備を完了する

## 作業内容

### 1. チェックリストの確認

#### コア機能

- [ ] ベクトルストアが正常に初期化される
- [ ] indexDocumentsツールが動作する（追加・更新）
- [ ] searchツールが動作する（セマンティック検索）
- [ ] deleteDocumentsツールが動作する（ID・フィルター）
- [ ] getCollectionInfoツールが動作する

#### MCP統合

- [ ] ListToolsRequestが正しく応答する
- [ ] CallToolRequestが全ツールで動作する
- [ ] ListResourcesRequestが正しく応答する
- [ ] ReadResourceRequestが全リソースで動作する
- [ ] ListPromptsRequestが正しく応答する
- [ ] GetPromptRequestが全プロンプトで動作する

#### ファイル監視

- [ ] ファイル追加時に自動インデックスされる
- [ ] ファイル変更時に自動更新される
- [ ] ファイル削除時にインデックスから削除される
- [ ] 無効化も正常に動作する

#### エラーハンドリング

- [ ] 全てのエラーが適切にハンドリングされる
- [ ] エラーメッセージが明確で実用的
- [ ] ログが適切に出力される
- [ ] グレースフルシャットダウンが機能する

#### テスト

- [ ] 全てのユニットテストがパスする
- [ ] 全ての統合テストがパスする
- [ ] テストカバレッジが70%以上
- [ ] パフォーマンステストがパスする

#### ドキュメント

- [ ] README.mdが完全で正確
- [ ] API.mdが最新
- [ ] ARCHITECTURE.mdが正確
- [ ] INSTALL.mdが機能する
- [ ] CHANGELOGが更新されている

#### デプロイメント

- [ ] package.jsonが正しく設定されている
- [ ] ビルドが成功する
- [ ] npm packが成功する
- [ ] Dockerビルドが成功する（オプション）
- [ ] postinstallスクリプトが動作する

### 2. エンドツーエンドテストスクリプトの作成

```bash
#!/bin/bash
# scripts/e2e-test.sh

set -e

echo "🧪 Starting End-to-End Tests..."
echo ""

# 1. クリーンビルド
echo "📦 Building project..."
npm run clean
npm run build

if [ ! -f "dist/index.js" ]; then
    echo "❌ Build failed: dist/index.js not found"
    exit 1
fi
echo "✅ Build successful"
echo ""

# 2. テストの実行
echo "🧪 Running tests..."
npm run test:coverage

if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi
echo "✅ All tests passed"
echo ""

# 3. サーバー起動テスト
echo "🚀 Testing server startup..."
timeout 10s npm run dev &
SERVER_PID=$!

sleep 5

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server started successfully"
    kill $SERVER_PID
else
    echo "❌ Server failed to start"
    exit 1
fi
echo ""

# 4. パッケージングテスト
echo "📦 Testing package..."
npm pack
if [ ! -f "semche-1.0.0.tgz" ]; then
    echo "❌ Package creation failed"
    exit 1
fi
echo "✅ Package created successfully"
rm semche-1.0.0.tgz
echo ""

# 5. 設定ファイルの確認
echo "📝 Checking configuration files..."
required_files=(".env.example" "tsconfig.json" "package.json" "jest.config.js")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done
echo "✅ All required files present"
echo ""

# 6. ドキュメントの確認
echo "📚 Checking documentation..."
required_docs=("README.md" "API.md" "ARCHITECTURE.md" "INSTALL.md" "CHANGELOG.md")

for doc in "${required_docs[@]}"; do
    if [ ! -f "$doc" ]; then
        echo "❌ Missing documentation: $doc"
        exit 1
    fi
done
echo "✅ All documentation present"
echo ""

echo "🎉 All End-to-End tests passed!"
echo ""
echo "Ready for release! 🚀"
```

### 3. リリース前チェックリスト

```markdown
# RELEASE_CHECKLIST.md

## リリース前チェックリスト

### コード品質

- [ ] 全てのテストがパスする
- [ ] テストカバレッジが70%以上
- [ ] ESLintエラーがゼロ
- [ ] TypeScriptエラーがゼロ
- [ ] ビルドエラーがゼロ

### 機能確認

- [ ] Cursor IDEからツールを呼び出せる
- [ ] ドキュメントのインデックスが正常
- [ ] 検索が正常に動作する
- [ ] リソースが参照できる
- [ ] プロンプトが使用できる

### ドキュメント

- [ ] READMEが最新
- [ ] APIドキュメントが最新
- [ ] インストール手順が正確
- [ ] トラブルシューティングガイドが役立つ
- [ ] CHANGELOGが更新されている

### パッケージング

- [ ] package.jsonのバージョンが正しい
- [ ] package.jsonの依存関係が最新
- [ ] LICENSEファイルがある
- [ ] .npmignoreが適切
- [ ] postinstallが動作する

### セキュリティ

- [ ] 依存関係に既知の脆弱性がない
- [ ] センシティブな情報が含まれていない
- [ ] .envファイルがgitignoreされている

### パフォーマンス

- [ ] 100ドキュメントのインデックスが30秒以内
- [ ] 100回の検索が20秒以内
- [ ] メモリリークがない

### 互換性

- [ ] Node.js 20以上で動作する
- [ ] Cursor IDE最新版で動作する
- [ ] Linux/macOS/Windowsで動作する（該当する場合）

### リリース準備

- [ ] バージョン番号を更新
- [ ] CHANGELOGにリリース日を記入
- [ ] GitHubリリースノートを準備
- [ ] npm公開の準備完了
```

### 4. パフォーマンスベンチマーク

```typescript
// scripts/benchmark.ts
import { indexDocuments } from "../src/tools/indexDocuments.js";
import { search } from "../src/tools/search.js";
import { closeVectorStore } from "../src/utils/vectorStore.js";

interface BenchmarkResult {
  operation: string;
  count: number;
  duration: number;
  avgTime: number;
  throughput: number;
}

async function runBenchmark(): Promise<void> {
  console.log("🏃 Running Performance Benchmarks...\n");

  const results: BenchmarkResult[] = [];

  // ベンチマーク1: インデックス速度
  console.log("📊 Benchmark 1: Indexing Performance");
  const indexDocs = Array.from({ length: 100 }, (_, i) => ({
    id: `bench-${i}`,
    content: `This is benchmark document number ${i}. It contains sample text for performance testing. The quick brown fox jumps over the lazy dog. Lorem ipsum dolor sit amet.`,
    metadata: {
      filePath: `/bench/doc${i}.txt`,
      language: "text",
    },
  }));

  const indexStart = Date.now();
  await indexDocuments({ documents: indexDocs, upsert: false });
  const indexDuration = Date.now() - indexStart;

  results.push({
    operation: "Indexing",
    count: 100,
    duration: indexDuration,
    avgTime: indexDuration / 100,
    throughput: (100 / indexDuration) * 1000,
  });

  console.log(`✅ Indexed 100 documents in ${indexDuration}ms`);
  console.log(`   Average: ${(indexDuration / 100).toFixed(2)}ms per document`);
  console.log(
    `   Throughput: ${((100 / indexDuration) * 1000).toFixed(2)} docs/sec\n`
  );

  // ベンチマーク2: 検索速度
  console.log("📊 Benchmark 2: Search Performance");
  const queries = [
    "benchmark document",
    "sample text",
    "quick brown fox",
    "lorem ipsum",
    "performance testing",
  ];

  const searchStart = Date.now();
  for (let i = 0; i < 100; i++) {
    await search({ query: queries[i % queries.length], k: 5 });
  }
  const searchDuration = Date.now() - searchStart;

  results.push({
    operation: "Search",
    count: 100,
    duration: searchDuration,
    avgTime: searchDuration / 100,
    throughput: (100 / searchDuration) * 1000,
  });

  console.log(`✅ Performed 100 searches in ${searchDuration}ms`);
  console.log(`   Average: ${(searchDuration / 100).toFixed(2)}ms per search`);
  console.log(
    `   Throughput: ${((100 / searchDuration) * 1000).toFixed(2)} searches/sec\n`
  );

  // 結果サマリー
  console.log("📈 Benchmark Summary:");
  console.log(
    "┌─────────────┬───────┬──────────┬─────────────┬────────────────┐"
  );
  console.log(
    "│ Operation   │ Count │ Duration │ Avg Time    │ Throughput     │"
  );
  console.log(
    "├─────────────┼───────┼──────────┼─────────────┼────────────────┤"
  );

  results.forEach((result) => {
    console.log(
      `│ ${result.operation.padEnd(11)} │ ${String(result.count).padEnd(5)} │ ${String(result.duration).padEnd(8)}ms │ ${result.avgTime.toFixed(2).padEnd(11)}ms │ ${result.throughput.toFixed(2).padEnd(14)}/s │`
    );
  });

  console.log(
    "└─────────────┴───────┴──────────┴─────────────┴────────────────┘\n"
  );

  await closeVectorStore();

  // パフォーマンス要件のチェック
  const indexingPassed = indexDuration < 30000;
  const searchPassed = searchDuration < 20000;

  if (indexingPassed && searchPassed) {
    console.log("✅ All performance benchmarks passed!");
  } else {
    console.log("❌ Some performance benchmarks failed:");
    if (!indexingPassed) console.log("   - Indexing too slow (>30s)");
    if (!searchPassed) console.log("   - Search too slow (>20s)");
    process.exit(1);
  }
}

runBenchmark().catch((error) => {
  console.error("❌ Benchmark failed:", error);
  process.exit(1);
});
```

### 5. package.jsonにスクリプトを追加

```json
{
  "scripts": {
    "e2e": "bash scripts/e2e-test.sh",
    "benchmark": "tsx scripts/benchmark.ts",
    "preflight": "npm run clean && npm run build && npm run test && npm run benchmark"
  }
}
```

### 6. 最終確認手順

```bash
# 1. 完全なクリーンビルド
npm run clean
npm install
npm run build

# 2. 全テストの実行
npm run test:coverage

# 3. E2Eテストの実行
chmod +x scripts/e2e-test.sh
npm run e2e

# 4. パフォーマンステストの実行
npm run benchmark

# 5. パッケージング
npm pack

# 6. 別ディレクトリでインストールテスト
mkdir ../semche-test
cd ../semche-test
npm install ../semche/semche-1.0.0.tgz
node node_modules/semche/dist/index.js --help

# 7. Cursor IDE統合テスト
# .cursor/mcp.jsonを設定してCursor IDEで動作確認
```

## 完了条件

- [ ] 全てのチェックリスト項目がチェックされている
- [ ] E2Eテストスクリプトが動作する
- [ ] パフォーマンステストがパスする
- [ ] パッケージが正常にインストールできる
- [ ] Cursor IDEで全機能が動作する
- [ ] ドキュメントが全て正確
- [ ] リリース準備が完了している

## リリース手順

### 1. バージョンの更新

```bash
# パッチバージョン（バグフィックス）
npm version patch

# マイナーバージョン（新機能）
npm version minor

# メジャーバージョン（破壊的変更）
npm version major
```

### 2. CHANGELOGの更新

- Unreleased → バージョン番号と日付
- 変更内容を整理

### 3. コミットとプッシュ

```bash
git push origin main --tags
```

### 4. GitHub Release

1. GitHubでReleaseを作成
2. タグを選択
3. リリースノートを記入
4. Publish release

### 5. npm公開（オプション）

```bash
npm login
npm publish
```

## トラブルシューティング

### テストが失敗する

- ログを確認: `tail -f logs/semche.log`
- データをクリア: `rm -rf data/chroma/*`
- 再ビルド: `npm run clean && npm run build`

### パッケージングエラー

- .npmignoreを確認
- dist/ディレクトリが存在するか確認
- 依存関係が正しくインストールされているか確認

### Cursor IDE統合が動作しない

- .cursor/mcp.jsonのパスを確認
- サーバーが起動するか個別にテスト: `npm run dev`
- Cursor IDEを完全に再起動

## 成功基準

- ✅ 全てのテストがパスする
- ✅ ドキュメントが完全で正確
- ✅ パッケージが正常にインストールできる
- ✅ Cursor IDEで全機能が動作する
- ✅ パフォーマンス要件を満たす
- ✅ エラーハンドリングが適切

## 次のステップ

実装フェーズへ移行！🚀
各タスクを順番に実装していきましょう。
