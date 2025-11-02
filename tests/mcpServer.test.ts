// tests/mcpServer.test.ts
import { describe, test, expect, beforeAll, afterAll } from "vitest";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { closeVectorStore } from "../src/utils/vectorStore";

describe("MCP Server", () => {
  afterAll(async () => {
    await closeVectorStore();
  });

  test("should create server instance", () => {
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

    expect(server).toBeDefined();
  });

  test("server should have correct metadata", () => {
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

    // サーバーが正しく初期化されていることを確認
    expect(server).toHaveProperty("connect");
    expect(server).toHaveProperty("setRequestHandler");
    expect(server).toHaveProperty("close");
  });
});
