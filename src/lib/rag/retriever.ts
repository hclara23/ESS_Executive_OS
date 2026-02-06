import type { Chunk } from "@/lib/rag/chunker";

export type Citation = {
  chunkId: string;
  snippet: string;
  score: number;
};

export type RetrievalResult = {
  answer: string;
  citations: Citation[];
};

const tokenize = (query: string) =>
  query
    .toLowerCase()
    .split(/[\s,.;:!?]+/)
    .filter(Boolean);

export function retrieveWithCitations(chunks: Chunk[], query: string): RetrievalResult {
  const tokens = tokenize(query);
  if (!tokens.length) {
    return { answer: "No query provided.", citations: [] };
  }

  const scored = chunks
    .map((chunk) => {
      const haystack = chunk.content.toLowerCase();
      const score = tokens.reduce((acc, token) => acc + (haystack.includes(token) ? 1 : 0), 0);
      return { chunk, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);

  const citations: Citation[] = scored.map(({ chunk, score }) => ({
    chunkId: chunk.id,
    score,
    snippet: chunk.content.slice(0, 160) + (chunk.content.length > 160 ? "…" : ""),
  }));

  const answer =
    citations.length > 0
      ? `Found ${citations.length} relevant knowledge chunks for "${query}".`
      : "No relevant knowledge found.";

  return { answer, citations };
}
