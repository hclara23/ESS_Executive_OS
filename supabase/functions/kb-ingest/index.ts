import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { corsHeaders } from "../_shared/cors.ts";
import { getServiceClient } from "../_shared/supabase.ts";

const chunkText = (text: string, maxChars = 800, overlap = 120) => {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) return [];
  const chunks = [];
  let start = 0;
  let index = 0;
  while (start < normalized.length) {
    const end = Math.min(start + maxChars, normalized.length);
    const content = normalized.slice(start, end).trim();
    if (content) {
      chunks.push({ index, content });
    }
    start = end - overlap;
    index += 1;
  }
  return chunks;
};

const fetchEmbedding = async (text: string) => {
  const endpoint = Deno.env.get("OPTIONAL_LLM_EMBEDDING_URL");
  if (!endpoint) return null;
  const apiKey = Deno.env.get("OPTIONAL_LLM_API_KEY");
  const model = Deno.env.get("OPTIONAL_LLM_MODEL");
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify({ input: text, model }),
  });
  if (!response.ok) return null;
  const data = await response.json();
  if (Array.isArray(data?.embedding)) return data.embedding;
  if (Array.isArray(data?.data) && data.data[0]?.embedding) {
    return data.data[0].embedding;
  }
  return null;
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const supabase = getServiceClient();
  const authHeader = req.headers.get("authorization") ?? "";
  const token = authHeader.replace("Bearer ", "");
  const {
    data: { user },
  } = token ? await supabase.auth.getUser(token) : { data: { user: null } };

  const body = await req.json();
  const content = body.content as string;
  if (!content) {
    return new Response(JSON.stringify({ error: "Missing content" }), {
      status: 400,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  let orgId = body.org_id as string | undefined;
  if (!orgId && user?.id) {
    const { data: orgMember } = await supabase
      .from("jarvis.org_members")
      .select("org_id")
      .eq("user_id", user.id)
      .limit(1)
      .maybeSingle();
    orgId = orgMember?.org_id;
  }

  if (!orgId) {
    return new Response(JSON.stringify({ error: "No org context" }), {
      status: 400,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const { data: doc, error: docError } = await supabase
    .from("jarvis.kb_documents")
    .insert({
      org_id: orgId,
      assistant_id: body.assistant_id ?? null,
      owner_user_id: user?.id ?? null,
      domain: body.domain ?? "WORK",
      visibility: body.visibility ?? "business_private",
      title: body.title ?? "Untitled",
      storage_path: body.storage_path ?? "",
      mime_type: body.mime_type ?? "text/plain",
      size_bytes: body.size_bytes ?? null,
    })
    .select()
    .single();

  if (docError) {
    return new Response(JSON.stringify({ error: docError.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const chunks = chunkText(content);
  if (chunks.length) {
    const rows = [];
    for (const chunk of chunks) {
      const embedding = await fetchEmbedding(chunk.content);
      rows.push({
        org_id: orgId,
        document_id: doc.id,
        assistant_id: body.assistant_id ?? null,
        owner_user_id: user?.id ?? null,
        domain: body.domain ?? "WORK",
        visibility: body.visibility ?? "business_private",
        chunk_index: chunk.index,
        content: chunk.content,
        token_count: Math.ceil(chunk.content.length / 4),
        embedding: embedding ?? null,
      });
    }
    await supabase.from("jarvis.kb_chunks").insert(rows);
  }

  return new Response(JSON.stringify({ status: "ok", chunkCount: chunks.length }), {
    status: 200,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
});
