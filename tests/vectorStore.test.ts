// tests/vectorStore.test.ts
import { describe, test, expect, afterAll } from "vitest";
import { getVectorStore, closeVectorStore } from "../src/utils/vectorStore";

describe("VectorStore", () => {
  afterAll(async () => {
    await closeVectorStore();
  });

  test("should initialize vector store", async () => {
    const vectorStore = await getVectorStore();
    expect(vectorStore).toBeDefined();
  });

  test("should return same instance (singleton)", async () => {
    const instance1 = await getVectorStore();
    const instance2 = await getVectorStore();
    expect(instance1).toBe(instance2);
  });
});
