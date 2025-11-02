// src/utils/textSplitter.ts
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

export interface ChunkOptions {
  chunkSize?: number;
  chunkOverlap?: number;
  separators?: string[];
}

/**
 * テキストをチャンクに分割
 */
export async function splitText(
  text: string,
  options: ChunkOptions = {}
): Promise<string[]> {
  const {
    chunkSize = 1000,
    chunkOverlap = 200,
    separators = ["\n\n", "\n", " ", ""],
  } = options;

  const splitter = new RecursiveCharacterTextSplitter({
    chunkSize,
    chunkOverlap,
    separators,
  });

  return await splitter.splitText(text);
}

/**
 * コード用のテキスト分割（より適切なセパレータ）
 */
export async function splitCode(
  code: string,
  language: string,
  options: ChunkOptions = {}
): Promise<string[]> {
  const codeSeparators: Record<string, string[]> = {
    typescript: ["\n\nclass ", "\n\nfunction ", "\n\nexport ", "\n\n", "\n"],
    javascript: ["\n\nclass ", "\n\nfunction ", "\n\nexport ", "\n\n", "\n"],
    python: ["\n\nclass ", "\n\ndef ", "\n\n", "\n"],
    default: ["\n\n", "\n", " ", ""],
  };

  const separators = codeSeparators[language] || codeSeparators.default;

  return splitText(code, { ...options, separators });
}
