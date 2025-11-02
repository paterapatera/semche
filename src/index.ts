// MCPサーバーのエントリポイント
import { config, validateConfig } from "./config.js";

console.log("MCP Server starting...");

// 設定の検証
try {
  validateConfig();
} catch (error) {
  console.error("Configuration error:", error);
  process.exit(1);
}
