# タスク10: MCPプロンプトの実装

## 目的

MCP (Model Context Protocol) のプロンプト機能を実装し、Cursor IDEで一般的な検索タスクのためのプロンプトテンプレートを提供する

## 作業内容

### 1. プロンプトハンドラーの作成

```typescript
// src/prompts/index.ts
import { logger } from "../utils/logger.js";

export interface PromptArgument {
  name: string;
  description: string;
  required: boolean;
}

export interface PromptDefinition {
  name: string;
  description: string;
  arguments: PromptArgument[];
}

/**
 * 利用可能なプロンプト一覧
 */
export const availablePrompts: PromptDefinition[] = [
  {
    name: "semantic-search",
    description:
      "Search the codebase semantically using natural language query",
    arguments: [
      {
        name: "query",
        description: "The search query in natural language",
        required: true,
      },
      {
        name: "context",
        description:
          "Additional context about what you're looking for (optional)",
        required: false,
      },
    ],
  },
  {
    name: "code-explanation",
    description: "Find code related to a specific functionality and explain it",
    arguments: [
      {
        name: "functionality",
        description: "The functionality you want to understand",
        required: true,
      },
    ],
  },
  {
    name: "similar-code",
    description: "Find code similar to a given code snippet or description",
    arguments: [
      {
        name: "codeOrDescription",
        description: "Code snippet or description of the code pattern",
        required: true,
      },
      {
        name: "language",
        description: "Programming language to filter by (optional)",
        required: false,
      },
    ],
  },
];

/**
 * semantic-search プロンプト
 */
export function getSemanticSearchPrompt(args: {
  query: string;
  context?: string;
}): string {
  logger.info("Generating semantic-search prompt", args);

  let prompt = `I want to search the codebase for: "${args.query}".\n\n`;

  if (args.context) {
    prompt += `Additional context: ${args.context}\n\n`;
  }

  prompt += `Please use the Semche vector search to find relevant code snippets and provide:\n`;
  prompt += `1. The most relevant code sections\n`;
  prompt += `2. File paths where the code is located\n`;
  prompt += `3. A brief explanation of how each result relates to my query\n\n`;
  prompt += `Use the following tool call:\n`;
  prompt += `\`\`\`json\n`;
  prompt += `{\n`;
  prompt += `  "tool": "search",\n`;
  prompt += `  "arguments": {\n`;
  prompt += `    "query": "${args.query}",\n`;
  prompt += `    "k": 5\n`;
  prompt += `  }\n`;
  prompt += `}\n`;
  prompt += `\`\`\``;

  return prompt;
}

/**
 * code-explanation プロンプト
 */
export function getCodeExplanationPrompt(args: {
  functionality: string;
}): string {
  logger.info("Generating code-explanation prompt", args);

  let prompt = `I want to understand how "${args.functionality}" is implemented in this codebase.\n\n`;
  prompt += `Please:\n`;
  prompt += `1. Search for code related to "${args.functionality}" using Semche\n`;
  prompt += `2. Explain the implementation approach\n`;
  prompt += `3. Highlight key files and functions involved\n`;
  prompt += `4. Mention any important patterns or dependencies\n\n`;
  prompt += `Use the search tool to find relevant code:\n`;
  prompt += `\`\`\`json\n`;
  prompt += `{\n`;
  prompt += `  "tool": "search",\n`;
  prompt += `  "arguments": {\n`;
  prompt += `    "query": "${args.functionality} implementation",\n`;
  prompt += `    "k": 5\n`;
  prompt += `  }\n`;
  prompt += `}\n`;
  prompt += `\`\`\``;

  return prompt;
}

/**
 * similar-code プロンプト
 */
export function getSimilarCodePrompt(args: {
  codeOrDescription: string;
  language?: string;
}): string {
  logger.info("Generating similar-code prompt", args);

  let prompt = `I want to find code similar to:\n\n`;
  prompt += `\`\`\`\n${args.codeOrDescription}\n\`\`\`\n\n`;
  prompt += `Please use Semche to find similar code patterns and provide:\n`;
  prompt += `1. Code snippets with similar logic or structure\n`;
  prompt += `2. Explanations of how each result is similar\n`;
  prompt += `3. Suggestions for code reuse or refactoring opportunities\n\n`;

  prompt += `Use the search tool:\n`;
  prompt += `\`\`\`json\n`;
  prompt += `{\n`;
  prompt += `  "tool": "search",\n`;
  prompt += `  "arguments": {\n`;
  prompt += `    "query": "${args.codeOrDescription.substring(0, 200)}",\n`;
  prompt += `    "k": 5`;

  if (args.language) {
    prompt += `,\n    "filter": { "language": "${args.language}" }`;
  }

  prompt += `\n  }\n`;
  prompt += `}\n`;
  prompt += `\`\`\``;

  return prompt;
}

/**
 * プロンプトを取得
 */
export function getPrompt(name: string, args: Record<string, string>): string {
  switch (name) {
    case "semantic-search":
      return getSemanticSearchPrompt(args);

    case "code-explanation":
      return getCodeExplanationPrompt(args);

    case "similar-code":
      return getSimilarCodePrompt(args);

    default:
      throw new Error(`Unknown prompt: ${name}`);
  }
}
```

### 2. MCPサーバーへのプロンプト統合

```typescript
// src/index.ts (ListPromptsRequestSchema と GetPromptRequestSchema を更新)
import { availablePrompts, getPrompt } from "./prompts/index.js";

/**
 * プロンプト一覧のハンドラー
 */
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  logger.info("Listing available prompts");

  return {
    prompts: availablePrompts.map((prompt) => ({
      name: prompt.name,
      description: prompt.description,
      arguments: prompt.arguments,
    })),
  };
});

/**
 * プロンプト取得のハンドラー
 */
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  logger.info(`Getting prompt: ${name}`, args);

  try {
    const promptText = getPrompt(name, args || {});

    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: promptText,
          },
        },
      ],
    };
  } catch (error) {
    logger.error(`Failed to get prompt: ${name}`, error);
    throw error;
  }
});
```

### 3. テストの作成

```typescript
// tests/prompts/prompts.test.ts
import {
  getSemanticSearchPrompt,
  getCodeExplanationPrompt,
  getSimilarCodePrompt,
  getPrompt,
} from "../../src/prompts/index";

describe("MCP Prompts", () => {
  describe("semantic-search", () => {
    test("should generate semantic search prompt", () => {
      const prompt = getSemanticSearchPrompt({
        query: "user authentication",
      });

      expect(prompt).toContain("user authentication");
      expect(prompt).toContain("search");
      expect(prompt).toContain('"tool": "search"');
    });

    test("should include context when provided", () => {
      const prompt = getSemanticSearchPrompt({
        query: "database connection",
        context: "looking for PostgreSQL setup",
      });

      expect(prompt).toContain("database connection");
      expect(prompt).toContain("PostgreSQL setup");
    });
  });

  describe("code-explanation", () => {
    test("should generate code explanation prompt", () => {
      const prompt = getCodeExplanationPrompt({
        functionality: "API rate limiting",
      });

      expect(prompt).toContain("API rate limiting");
      expect(prompt).toContain("implementation");
      expect(prompt).toContain('"tool": "search"');
    });
  });

  describe("similar-code", () => {
    test("should generate similar code prompt", () => {
      const prompt = getSimilarCodePrompt({
        codeOrDescription: "async function fetchData() { ... }",
      });

      expect(prompt).toContain("async function fetchData");
      expect(prompt).toContain("similar");
      expect(prompt).toContain('"tool": "search"');
    });

    test("should include language filter when provided", () => {
      const prompt = getSimilarCodePrompt({
        codeOrDescription: "function example",
        language: "typescript",
      });

      expect(prompt).toContain("typescript");
      expect(prompt).toContain('"filter"');
    });
  });

  describe("getPrompt", () => {
    test("should route to correct prompt handler", () => {
      const prompt = getPrompt("semantic-search", {
        query: "test query",
      });

      expect(prompt).toContain("test query");
    });

    test("should throw error for unknown prompt", () => {
      expect(() => {
        getPrompt("unknown-prompt", {});
      }).toThrow("Unknown prompt: unknown-prompt");
    });
  });
});
```

### 4. Cursor IDEでの使用例

Cursorチャットで以下のようにプロンプトを使用:

```
/prompt semantic-search query:"ユーザー認証の実装"
```

```
/prompt code-explanation functionality:"データベース接続"
```

```
/prompt similar-code codeOrDescription:"async/await パターン" language:"typescript"
```

または、Cursor IDE組み込みのプロンプトピッカーから選択:

1. チャット入力欄で `/` を入力
2. 「prompt」を選択
3. 利用可能なプロンプトから選択
4. 引数を入力

## 完了条件

- [ ] src/prompts/index.tsが実装されている
- [ ] MCPサーバーにプロンプトが統合されている
- [ ] 3つのプロンプト（semantic-search, code-explanation, similar-code）が全て機能する
- [ ] ListPromptsRequestが正しく応答する
- [ ] GetPromptRequestが正しく応答する
- [ ] テストが全てパスする
- [ ] Cursor IDEからプロンプトを使用できる

## 動作確認

### ローカルテスト

```bash
npm run test -- tests/prompts/prompts.test.ts
```

### Cursor IDEでの確認

1. サーバーを起動: `npm run dev`
2. Cursor IDEを再起動
3. チャットで `/prompt` と入力
4. 3つのプロンプトが表示されることを確認
5. プロンプトを選択して引数を入力
6. 生成されたプロンプトで検索が実行されることを確認

## プロンプトの使い道

### semantic-search

- 自然言語でのコード検索
- 機能の実装場所を特定
- 既存コードの発見

### code-explanation

- コードの動作を理解
- 実装の詳細を学習
- ドキュメント作成の補助

### similar-code

- 重複コードの発見
- リファクタリング候補の特定
- コードパターンの再利用

## トラブルシューティング

- プロンプトが表示されない: ListPromptsRequestハンドラーを確認
- 引数が認識されない: 引数の定義とrequiredフラグを確認
- プロンプトが機能しない: GetPromptRequestハンドラーのログを確認

## 次のタスク

タスク11: ファイル監視機能の実装
