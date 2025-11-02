# logger.ts - コード説明ドキュメント

## 概要

このファイルは、MCPサーバー向けのロギングユーティリティを提供します。標準出力(`stdout`)をMCPプロトコルの通信に使用するため、すべてのログは標準エラー出力(`stderr`)に出力される設計になっています。

## 依存クラス・モジュール一覧

このファイルは外部のクラスやモジュールに依存していません。Node.jsの組み込み機能のみを使用しています。

| 機能            | 種類               | パス/説明                  |
| --------------- | ------------------ | -------------------------- |
| `console.error` | Node.js組み込み    | 標準エラー出力への書き込み |
| `Date`          | JavaScript組み込み | タイムスタンプ生成         |
| `JSON`          | JavaScript組み込み | オブジェクトのJSON変換     |

## エクスポートされる要素

### LogLevel (enum)

ログレベルを定義する列挙型です。

```typescript
export enum LogLevel {
  ERROR = "error",
  WARN = "warn",
  INFO = "info",
  DEBUG = "debug",
}
```

**利用可能なログレベル:**

- `ERROR`: エラーレベルのログ
- `WARN`: 警告レベルのログ
- `INFO`: 情報レベルのログ
- `DEBUG`: デバッグレベルのログ

### log関数

基本的なログ出力機能を提供する関数です。

**シグネチャ:**

```typescript
export function log(level: LogLevel, message: string, data?: any): void;
```

**パラメータ:**

- `level`: ログレベル (LogLevel enum)
- `message`: ログメッセージ (文字列)
- `data`: オプションの追加データ (任意の型)

**動作:**

1. ISO 8601形式のタイムスタンプを生成
2. `[タイムスタンプ] [ログレベル] メッセージ` の形式でログをフォーマット
3. `stderr`にログメッセージを出力
4. `data`が提供されている場合、JSON形式(インデント2スペース)で`stderr`に出力

**出力例:**

```
[2025-11-02T02:37:59.123Z] [INFO] サーバーが起動しました
[2025-11-02T02:38:01.456Z] [ERROR] データベース接続エラー
{
  "host": "localhost",
  "port": 5432
}
```

**重要なポイント:**

- MCPサーバーは`stdout`を通信に使用するため、ログは必ず`stderr`に出力されます
- タイムスタンプはUTC時刻(ISO 8601形式)で記録されます
- 追加データは整形されたJSON形式で出力されます

### logger オブジェクト

便利なロギングメソッドを提供するオブジェクトです。各メソッドは対応するログレベルで`log`関数を呼び出します。

**エクスポート:**

```typescript
export const logger = {
  error: (message: string, data?: any) => log(LogLevel.ERROR, message, data),
  warn: (message: string, data?: any) => log(LogLevel.WARN, message, data),
  info: (message: string, data?: any) => log(LogLevel.INFO, message, data),
  debug: (message: string, data?: any) => log(LogLevel.DEBUG, message, data),
};
```

**利用可能なメソッド:**

| メソッド         | ログレベル | 用途                                 |
| ---------------- | ---------- | ------------------------------------ |
| `logger.error()` | ERROR      | エラー、例外、致命的な問題           |
| `logger.warn()`  | WARN       | 警告、非推奨機能の使用、潜在的な問題 |
| `logger.info()`  | INFO       | 一般的な情報、動作状況               |
| `logger.debug()` | DEBUG      | デバッグ情報、詳細なトレース         |

**使用例:**

```typescript
import { logger } from "./logger.js";

// シンプルなログ
logger.info("サーバーが起動しました");

// データ付きログ
logger.error("データベース接続エラー", {
  host: "localhost",
  port: 5432,
  error: "ECONNREFUSED",
});

// デバッグ情報
logger.debug("リクエスト処理中", {
  requestId: "abc123",
  timestamp: Date.now(),
  method: "GET",
  path: "/api/users",
});

// 警告
logger.warn("非推奨のAPIが使用されました", {
  endpoint: "/old/api",
  deprecatedSince: "v2.0.0",
});
```

## 設計上の注意点

### 1. stdout vs stderr

**重要:** MCPサーバーの仕様上、`stdout`はプロトコル通信専用です。

- ✅ **正しい**: すべてのログ出力は`stderr`を使用
- ❌ **誤り**: `console.log()`を使用すると通信が破壊される

```typescript
// ✅ 正しい
console.error("[INFO] サーバー起動");
logger.info("サーバー起動");

// ❌ 誤り - MCPプロトコルを破壊する
console.log("[INFO] サーバー起動");
```

### 2. タイムスタンプ形式

ISO 8601形式を使用することで、国際的に認識可能な標準的なタイムスタンプを提供します。

```typescript
new Date().toISOString();
// 出力例: "2025-11-02T02:37:59.123Z"
```

### 3. JSON出力

追加データは構造化されたJSON形式で出力されるため、ログ解析ツールでの処理が容易です。

```typescript
JSON.stringify(data, null, 2);
// インデント2スペースで読みやすく整形
```

### 4. 型安全性

TypeScriptのenumを使用することで、ログレベルの型安全性を確保しています。

```typescript
// ✅ 型安全
log(LogLevel.INFO, "message");

// ❌ コンパイルエラー
log("invalid", "message");
```

## 使用箇所

このロガーは以下のファイルで使用されています：

| ファイルパス               | 用途                             |
| -------------------------- | -------------------------------- |
| `src/config.ts`            | 設定の検証ログ                   |
| `src/utils/vectorStore.ts` | ベクトルストアの初期化・操作ログ |
| `src/index.ts`             | サーバーの起動・エラーログ       |

## 改善提案

現在のコードは明確でシンプルですが、以下の機能追加を検討できます:

### 1. ログレベルフィルタリング

環境変数によるログレベルの制御:

```typescript
const currentLogLevel = process.env.LOG_LEVEL || "info";

export function log(level: LogLevel, message: string, data?: any): void {
  // レベルチェック
  if (!shouldLog(level, currentLogLevel)) return;

  // ... 既存のログ処理
}
```

### 2. ログフォーマットのカスタマイズ

JSON形式やプレーンテキスト形式の切り替え:

```typescript
const format = process.env.LOG_FORMAT || "text"; // "text" | "json"
```

### 3. パフォーマンス測定

処理時間の計測機能:

```typescript
logger.timer("処理開始");
// ... 処理
logger.timerEnd("処理開始"); // "処理開始: 123ms"
```

### 4. コンテキスト情報

リクエストIDなどのコンテキストを自動付与:

```typescript
logger.withContext({ requestId: "abc123" }).info("処理開始");
```

## まとめ

このロギングユーティリティは、MCPサーバーの要件に適合したシンプルで効果的なログ機能を提供します。型安全性、読みやすい出力、そしてMCPプロトコルとの互換性を重視した設計になっています。
