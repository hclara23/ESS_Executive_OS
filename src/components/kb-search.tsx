"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Citation = {
  chunkId: string;
  snippet: string;
  documentId: string;
};

export function KbSearch() {
  const [query, setQuery] = React.useState("");
  const [result, setResult] = React.useState<string | null>(null);
  const [citations, setCitations] = React.useState<Citation[]>([]);
  const [loading, setLoading] = React.useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    setCitations([]);
    const response = await fetch("/api/rag", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await response.json();
    setResult(data.answer ?? "No response.");
    setCitations(data.citations ?? []);
    setLoading(false);
  };

  return (
    <Card className="glass-card p-5">
      <div className="text-sm font-semibold">Query Knowledge</div>
      <div className="mt-3 text-xs text-muted-foreground">
        Retrieval returns ranked citations.
      </div>
      <div className="mt-4 flex gap-2">
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask a question about ESS knowledge..."
        />
        <Button onClick={handleSearch} disabled={loading} className="rounded-full">
          <Search className="mr-2 h-4 w-4" />
          {loading ? "Searching" : "Search"}
        </Button>
      </div>
      {result && (
        <div className="mt-4 rounded-2xl border border-border/50 bg-background/60 p-4 text-sm">
          <div className="font-semibold">Answer</div>
          <div className="mt-2 text-muted-foreground">{result}</div>
        </div>
      )}
      {citations.length > 0 && (
        <div className="mt-4 space-y-2 text-xs text-muted-foreground">
          <div className="font-semibold uppercase tracking-[0.2em]">Citations</div>
          {citations.map((cite) => (
            <div key={cite.chunkId} className="rounded-xl border border-border/50 p-3">
              <div>{cite.snippet}</div>
              <div className="mt-2 text-[10px]">Chunk: {cite.chunkId}</div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
