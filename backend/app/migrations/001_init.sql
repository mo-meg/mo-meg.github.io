-- Knowledge base schema. {embedding_dim} is substituted from EMBEDDING_DIM at migration time.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id              BIGSERIAL PRIMARY KEY,
    source_id       TEXT        NOT NULL UNIQUE,
    title           TEXT        NOT NULL,
    source_label    TEXT        NOT NULL,
    category        TEXT        NOT NULL,
    url             TEXT,
    content_hash    TEXT        NOT NULL,
    embedding_model TEXT        NOT NULL,
    metadata        JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS documents_category_idx ON documents (category);
CREATE INDEX IF NOT EXISTS documents_text_hash_idx ON documents ((metadata->>'text_hash'));

CREATE TABLE IF NOT EXISTS chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  BIGINT  NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index  INTEGER NOT NULL,
    heading      TEXT    NOT NULL DEFAULT '',
    content      TEXT    NOT NULL,
    content_hash TEXT    NOT NULL,
    embedding    vector({embedding_dim}) NOT NULL,
    tsv          tsvector GENERATED ALWAYS AS (to_tsvector('english', heading || ' ' || content)) STORED,
    UNIQUE (document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv);
