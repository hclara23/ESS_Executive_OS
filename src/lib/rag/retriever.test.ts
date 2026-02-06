import { describe, expect, it } from "vitest";
import { retrieveWithCitations } from "@/lib/rag/retriever";
import type { Chunk } from "@/lib/rag/chunker";

describe("RAG retrieval", () => {
  it("returns citations for relevant chunks", () => {
    const chunks: Chunk[] = [
      { id: "c1", index: 0, content: "ESS pricing policy updated for 2026.", tokens: 6 },
      { id: "c2", index: 1, content: "HR handbook covers leave and benefits.", tokens: 7 },
    ];

    const result = retrieveWithCitations(chunks, "pricing policy");
    expect(result.citations.length).toBeGreaterThan(0);
    expect(result.citations[0].chunkId).toBe("c1");
  });
});
