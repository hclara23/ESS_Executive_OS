import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabase/server";
import { getSupabaseAdminClient } from "@/lib/supabase/admin";

async function fetchEmbedding(query: string) {
  const endpoint = process.env.OPTIONAL_LLM_EMBEDDING_URL;
  if (!endpoint) return null;
  const apiKey = process.env.OPTIONAL_LLM_API_KEY;
  const model = process.env.OPTIONAL_LLM_MODEL;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify({ input: query, model }),
  });
  if (!response.ok) return null;
  const data = await response.json();
  if (Array.isArray(data?.embedding)) return data.embedding;
  if (Array.isArray(data?.data) && data.data[0]?.embedding) {
    return data.data[0].embedding;
  }
  return null;
}

export async function POST(req: Request) {
  const supabase = await getSupabaseServerClient();
  if (!supabase) {
    return NextResponse.json({ error: "Supabase not configured." }, { status: 500 });
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const query = (body.query ?? "").toString().trim();
  if (!query) {
    return NextResponse.json({ error: "Missing query" }, { status: 400 });
  }

  const admin = getSupabaseAdminClient();
  const { data: orgMembership } = await admin
    .from("jarvis.org_members")
    .select("org_id")
    .eq("user_id", user.id)
    .limit(1)
    .maybeSingle();

  if (!orgMembership?.org_id) {
    return NextResponse.json({ error: "No org membership" }, { status: 403 });
  }

  const { data: chunks, error } = await admin
    .from("jarvis.kb_chunks")
    .select("id, content, document_id, created_at")
    .eq("org_id", orgMembership.org_id)
    .textSearch("keyword_tsv", query)
    .limit(4);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  type VectorRow = { id: string; content: string; document_id: string; similarity: number };
  let vectorChunks: { id: string; content: string; document_id: string }[] = [];
  const embedding = await fetchEmbedding(query);
  if (embedding) {
    const rpcResult = await admin.rpc("match_kb_chunks", {
      query_embedding: embedding,
      match_count: 4,
      match_org_id: orgMembership.org_id,
    });
    const vectorData = (rpcResult.data ?? []) as VectorRow[];
    vectorChunks = vectorData.map((row: VectorRow) => ({
      id: row.id,
      content: row.content,
      document_id: row.document_id,
    }));
  }

  const merged = [...(chunks ?? []), ...vectorChunks].reduce(
    (acc, chunk) => {
      if (!acc.map.has(chunk.id)) {
        acc.map.set(chunk.id, chunk);
        acc.list.push(chunk);
      }
      return acc;
    },
    {
      list: [] as { id: string; content: string; document_id: string; created_at?: string }[],
      map: new Map<string, { id: string; content: string; document_id: string }>(),
    },
  ).list;

  const citations =
    merged?.map((chunk) => ({
      chunkId: chunk.id,
      snippet:
        chunk.content.slice(0, 160) + (chunk.content.length > 160 ? "…" : ""),
      documentId: chunk.document_id,
    })) ?? [];

  return NextResponse.json({
    answer:
      citations.length > 0
        ? `Found ${citations.length} relevant chunks for "${query}".`
        : "No relevant knowledge found.",
    citations,
  });
}
