// src/utils/logger.ts
export enum LogLevel {
  ERROR = "error",
  WARN = "warn",
  INFO = "info",
  DEBUG = "debug",
}

export function log(level: LogLevel, message: string, data?: any): void {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

  // MCPサーバーはstdoutを使用するため、ログはstderrに出力
  console.error(logMessage);

  if (data) {
    console.error(JSON.stringify(data, null, 2));
  }
}

export const logger = {
  error: (message: string, data?: any) => log(LogLevel.ERROR, message, data),
  warn: (message: string, data?: any) => log(LogLevel.WARN, message, data),
  info: (message: string, data?: any) => log(LogLevel.INFO, message, data),
  debug: (message: string, data?: any) => log(LogLevel.DEBUG, message, data),
};
