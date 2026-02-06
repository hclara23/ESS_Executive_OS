export type Chunk = {
  id: string;
  index: number;
  content: string;
  tokens: number;
  metadata?: Record<string, unknown>;
};

const estimateTokens = (text: string) => Math.max(1, Math.ceil(text.length / 4));

export function chunkText(
  text: string,
  options: { maxChars?: number; overlap?: number } = {},
): Chunk[] {
  const maxChars = options.maxChars ?? 800;
  const overlap = options.overlap ?? 120;
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) return [];

  const chunks: Chunk[] = [];
  let start = 0;
  let index = 0;
  while (start < normalized.length) {
    const end = Math.min(start + maxChars, normalized.length);
    const content = normalized.slice(start, end).trim();
    if (content) {
      chunks.push({
        id: `${index}-${content.slice(0, 16).replace(/\W/g, "")}`,
        index,
        content,
        tokens: estimateTokens(content),
      });
    }
    start = end - overlap;
    index += 1;
  }
  return chunks;
}
