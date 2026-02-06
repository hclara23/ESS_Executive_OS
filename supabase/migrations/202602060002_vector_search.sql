create or replace function jarvis.match_kb_chunks(
  query_embedding vector(1536),
  match_count int,
  match_org_id uuid
)
returns table (
  id uuid,
  content text,
  document_id uuid,
  similarity float
)
language sql
stable
as $$
  select
    kb.id,
    kb.content,
    kb.document_id,
    1 - (kb.embedding <=> query_embedding) as similarity
  from jarvis.kb_chunks kb
  where kb.org_id = match_org_id
    and kb.embedding is not null
  order by kb.embedding <=> query_embedding
  limit match_count;
$$;
