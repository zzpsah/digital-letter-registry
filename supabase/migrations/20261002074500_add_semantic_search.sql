-- Semantic search foundation using 768-dimensional pgvector embeddings.
-- Safe to re-embed because embedding_version remains explicit.

alter table public.letter_chunks
  alter column embedding type extensions.vector(768)
  using embedding::extensions.vector(768);

create index if not exists letter_chunks_embedding_hnsw_idx
  on public.letter_chunks
  using hnsw (embedding extensions.vector_cosine_ops)
  where embedding is not null;

create or replace function public.search_letter_chunks_semantic(
  query_embedding extensions.vector(768),
  query_embedding_version text,
  result_limit integer default 25
)
returns table (
  letter_id uuid,
  chunk_index integer,
  content text,
  semantic_similarity real
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  select
    c.letter_id,
    c.chunk_index,
    c.content,
    (1 - (c.embedding <=> query_embedding))::real as semantic_similarity
  from public.letter_chunks c
  where c.embedding is not null
    and c.embedding_version = query_embedding_version
  order by c.embedding <=> query_embedding
  limit greatest(1, least(coalesce(result_limit, 25), 100));
$$;

grant execute on function public.search_letter_chunks_semantic(
  extensions.vector(768),
  text,
  integer
) to authenticated;
