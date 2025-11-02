# textSplitter.ts - コード説明ドキュメント

## 概要

このファイルは、テキストやコードをベクトル検索に適したサイズのチャンク（断片）に分割するユーティリティを提供します。LangChainの`RecursiveCharacterTextSplitter`を使用して、文脈を保持しながら効率的にテキストを分割します。

## 依存クラス・モジュール一覧

| クラス/モジュール                | インポート元               | ファイルパス                                                  | 説明                             |
| -------------------------------- | -------------------------- | ------------------------------------------------------------- | -------------------------------- |
| `RecursiveCharacterTextSplitter` | `@langchain/textsplitters` | `node_modules/@langchain/textsplitters/dist/text_splitter.js` | 再帰的にテキストを分割するクラス |

## エクスポートされる要素

### ChunkOptions (interface)

テキスト分割のオプションを定義するインターフェースです。

```typescript
export interface ChunkOptions {
  chunkSize?: number;
  chunkOverlap?: number;
  separators?: string[];
}
```

**プロパティ:**

| プロパティ     | 型         | デフォルト値              | 説明                                     |
| -------------- | ---------- | ------------------------- | ---------------------------------------- |
| `chunkSize`    | `number`   | `1000`                    | 各チャンクの最大文字数                   |
| `chunkOverlap` | `number`   | `200`                     | 隣接するチャンク間の重複文字数           |
| `separators`   | `string[]` | `["\n\n", "\n", " ", ""]` | 分割に使用する区切り文字の優先順位リスト |

**チャンクオーバーラップの重要性:**

オーバーラップは文脈の連続性を保つために重要です。例えば：

```
チャンク1: "...この関数は重要な処理を行います。"
                                    ↓ 200文字の重複
チャンク2:              "処理を行います。次に別の処理が..."
```

これにより、チャンク境界で情報が途切れることを防ぎます。

### splitText 関数

汎用的なテキスト分割関数です。

**シグネチャ:**

```typescript
export async function splitText(
  text: string,
  options: ChunkOptions = {}
): Promise<string[]>;
```

**パラメータ:**

- `text`: 分割対象のテキスト（文字列）
- `options`: 分割オプション（省略可能）

**戻り値:**

- `Promise<string[]>`: 分割されたテキストチャンクの配列

**デフォルト設定:**

- チャンクサイズ: 1000文字
- オーバーラップ: 200文字
- セパレータ: `["\n\n", "\n", " ", ""]`（段落 → 行 → 単語 → 文字の順で分割を試みる）

**動作の仕組み:**

1. **セパレータの優先順位**: リストの最初のセパレータから順に分割を試みます
   - `"\n\n"`: 段落単位で分割（最も優先）
   - `"\n"`: 行単位で分割
   - `" "`: 単語単位で分割
   - `""`: 文字単位で強制分割（最終手段）

2. **再帰的分割**: チャンクサイズを超える場合、次のセパレータで再帰的に分割

**使用例:**

```typescript
// 基本的な使用
const text = "長いテキスト...";
const chunks = await splitText(text);

// カスタムオプション
const chunks = await splitText(text, {
  chunkSize: 500,
  chunkOverlap: 100,
  separators: ["\n", " ", ""],
});

// マークダウンドキュメントの分割
const markdown = "# タイトル\n\n段落1...\n\n段落2...";
const chunks = await splitText(markdown, {
  separators: ["\n\n", "\n# ", "\n## ", "\n", " ", ""],
});
```

### splitCode 関数

プログラミング言語のコードに最適化された分割関数です。

**シグネチャ:**

```typescript
export async function splitCode(
  code: string,
  language: string,
  options: ChunkOptions = {}
): Promise<string[]>;
```

**パラメータ:**

- `code`: 分割対象のコード（文字列）
- `language`: プログラミング言語名（`"typescript"`, `"javascript"`, `"python"`, その他）
- `options`: 分割オプション（省略可能）

**戻り値:**

- `Promise<string[]>`: 分割されたコードチャンクの配列

**言語別セパレータ:**

| 言語       | セパレータ（優先順位順）                                       | 説明                                     |
| ---------- | -------------------------------------------------------------- | ---------------------------------------- |
| TypeScript | `["\n\nclass ", "\n\nfunction ", "\n\nexport ", "\n\n", "\n"]` | クラス、関数、エクスポート単位で優先分割 |
| JavaScript | `["\n\nclass ", "\n\nfunction ", "\n\nexport ", "\n\n", "\n"]` | TypeScriptと同じ                         |
| Python     | `["\n\nclass ", "\n\ndef ", "\n\n", "\n"]`                     | クラス、関数定義単位で優先分割           |
| その他     | `["\n\n", "\n", " ", ""]`                                      | デフォルトのセパレータ                   |

**設計思想:**

コードは文法的な単位で分割することで、意味のあるチャンクを作成します：

1. **クラス単位**: クラス全体を1つのチャンクに保つ
2. **関数単位**: 関数全体を1つのチャンクに保つ
3. **エクスポート単位**: モジュールのエクスポート宣言を優先
4. **段落・行単位**: 上記で分割できない場合のフォールバック

**使用例:**

```typescript
// TypeScriptコードの分割
const tsCode = `
export class MyClass {
  method() {
    // ...
  }
}

export function myFunction() {
  // ...
}
`;

const chunks = await splitCode(tsCode, "typescript");
// 結果: ["export class MyClass {...}", "export function myFunction() {...}"]

// Pythonコードの分割
const pyCode = `
class MyClass:
    def method(self):
        pass

def my_function():
    pass
`;

const chunks = await splitCode(pyCode, "python", {
  chunkSize: 500,
  chunkOverlap: 50,
});

// 未対応言語（デフォルトセパレータを使用）
const rubyCode = "...";
const chunks = await splitCode(rubyCode, "ruby");
```

## 使用箇所

このテキストスプリッターは以下のファイルで使用される予定です：

| ファイルパス                       | 用途                                           |
| ---------------------------------- | ---------------------------------------------- |
| `src/tools/index.ts`（予定）       | ドキュメントのインデックス化時にテキストを分割 |
| `src/tools/search.ts`（予定）      | 検索前の前処理として使用                       |
| `src/utils/vectorStore.ts`（予定） | ベクトル化前のテキスト準備                     |

## 技術的な詳細

### RecursiveCharacterTextSplitterの仕組み

LangChainの`RecursiveCharacterTextSplitter`は以下のアルゴリズムで動作します：

1. **セパレータによる分割**: 指定されたセパレータで最初の分割を試みる
2. **サイズチェック**: 分割されたチャンクがchunkSizeを超えているか確認
3. **再帰的処理**: 超えている場合、次のセパレータで再帰的に分割
4. **オーバーラップの追加**: 隣接するチャンクにchunkOverlap分の重複を追加
5. **結合**: 小さすぎるチャンクは結合して効率化

### なぜオーバーラップが必要か

ベクトル検索では、文脈が重要です。オーバーラップがないと：

```
❌ オーバーラップなし:
チャンク1: "関数Aは重要な処理を行い"
チャンク2: "結果をデータベースに保存します"
→ どちらのチャンクにも「何を保存するか」の情報が不完全

✅ オーバーラップあり:
チャンク1: "関数Aは重要な処理を行い、結果を"
チャンク2: "結果をデータベースに保存します"
→ チャンク2は「結果」が何かを理解できる
```

### パフォーマンスの考慮

- **チャンクサイズ**: 小さすぎると文脈が失われ、大きすぎると検索精度が下がる
- **推奨値**: 一般的なテキストは800-1200文字、コードは500-1000文字
- **オーバーラップ率**: 通常はチャンクサイズの10-20%（100-200文字）

## 使用上の注意点

### 1. 非同期処理

両関数とも非同期（async）なので、必ず`await`を使用してください：

```typescript
// ✅ 正しい
const chunks = await splitText(text);

// ❌ 誤り
const chunks = splitText(text); // Promiseオブジェクトが返る
```

### 2. 言語名の指定

`splitCode`の言語名は小文字で指定してください：

```typescript
// ✅ 正しい
await splitCode(code, "typescript");
await splitCode(code, "python");

// ⚠️ 動作するが推奨しない
await splitCode(code, "TypeScript"); // defaultセパレータが使われる
```

### 3. メモリ使用量

大きなファイルを分割する場合、メモリ使用量に注意：

```typescript
// 大きなファイルの場合
const largeText = fs.readFileSync("large-file.txt", "utf-8");
const chunks = await splitText(largeText, {
  chunkSize: 2000, // より大きなチャンクで分割数を減らす
  chunkOverlap: 100,
});
```

## 改善提案

### 1. より多くの言語サポート

```typescript
const codeSeparators: Record<string, string[]> = {
  // 既存の言語
  typescript: [...],
  javascript: [...],
  python: [...],

  // 追加候補
  java: ["\n\nclass ", "\n\npublic ", "\n\nprivate ", "\n\n", "\n"],
  go: ["\n\nfunc ", "\n\ntype ", "\n\n", "\n"],
  rust: ["\n\nfn ", "\n\nimpl ", "\n\nstruct ", "\n\n", "\n"],
  ruby: ["\n\nclass ", "\n\ndef ", "\n\nmodule ", "\n\n", "\n"],
};
```

### 2. カスタムセパレータのサポート

```typescript
export async function splitCodeCustom(
  code: string,
  customSeparators: string[],
  options: ChunkOptions = {}
): Promise<string[]>;
```

### 3. チャンク情報の保持

```typescript
interface ChunkWithMetadata {
  content: string;
  index: number;
  startChar: number;
  endChar: number;
}

export async function splitTextWithMetadata(
  text: string,
  options: ChunkOptions = {}
): Promise<ChunkWithMetadata[]>;
```

### 4. ストリーミング対応

大きなファイル用にストリーミング分割：

```typescript
export async function* splitTextStream(
  text: string,
  options: ChunkOptions = {}
): AsyncGenerator<string>
```

## まとめ

このテキストスプリッターは、ベクトル検索システムにおいて重要な役割を果たします。適切なチャンクサイズとオーバーラップにより、検索精度を最大化しつつ、パフォーマンスを維持します。コード専用の分割機能により、プログラミング言語の文法を考慮した意味のある分割が可能です。
