-- db/init/001_pgvector.sql
CREATE EXTENSION IF NOT EXISTS vector;

-- chunk for all entities (product, category, order, customer, employee)
CREATE TABLE IF NOT EXISTS admin_chunk (
  id BIGSERIAL PRIMARY KEY,
  entity_type TEXT CHECK (entity_type IN ('product','category','order','customer','employee')),
  entity_id BIGINT NOT NULL,
  source TEXT,
  text TEXT NOT NULL,
  embedding VECTOR(1536)
);

-- accelerate search
CREATE INDEX IF NOT EXISTS admin_chunk_embedding_idx
ON admin_chunk USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
