CREATE OR REPLACE FUNCTION match_it_documents (
  query_embedding vector(768),
  match_count int default null,
  filter jsonb DEFAULT '{}'
) returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    it_documents.id,
    it_documents.content,
    it_documents.metadata,
    1 - (it_documents.embedding <=> query_embedding) as similarity
  from it_documents
  where it_documents.metadata @> filter
  order by it_documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
