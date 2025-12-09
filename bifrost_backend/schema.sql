-- Bifrost Database Schema

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Tools table
CREATE TABLE IF NOT EXISTS tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    input_schema JSONB NOT NULL,
    category TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tools_tags ON tools USING GIN(tags) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tools_embedding ON tools USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100) WHERE deleted_at IS NULL AND embedding IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tools_created_at ON tools(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name) WHERE deleted_at IS NULL;

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_tools_description_fts ON tools USING GIN(to_tsvector('english', description)) WHERE deleted_at IS NULL;

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_tools_updated_at ON tools;
CREATE TRIGGER update_tools_updated_at
    BEFORE UPDATE ON tools
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO tools (name, description, input_schema, category, tags, metadata)
VALUES
    (
        'create_entity',
        'Creates a new entity in the knowledge graph with specified properties',
        '{"type":"object","properties":{"name":{"type":"string","description":"Entity name"},"type":{"type":"string","description":"Entity type"},"properties":{"type":"object","description":"Additional properties"}},"required":["name","type"]}',
        'knowledge_graph',
        ARRAY['entity', 'create', 'knowledge'],
        '{"version":"1.0","author":"system"}'
    ),
    (
        'search_entities',
        'Searches for entities in the knowledge graph based on query criteria',
        '{"type":"object","properties":{"query":{"type":"string","description":"Search query"},"type":{"type":"string","description":"Filter by entity type"},"limit":{"type":"number","description":"Max results","default":10}},"required":["query"]}',
        'knowledge_graph',
        ARRAY['entity', 'search', 'query'],
        '{"version":"1.0","author":"system"}'
    ),
    (
        'create_relationship',
        'Creates a relationship between two entities in the knowledge graph',
        '{"type":"object","properties":{"source_id":{"type":"string","description":"Source entity ID"},"target_id":{"type":"string","description":"Target entity ID"},"relationship_type":{"type":"string","description":"Type of relationship"},"properties":{"type":"object","description":"Relationship properties"}},"required":["source_id","target_id","relationship_type"]}',
        'knowledge_graph',
        ARRAY['relationship', 'create', 'graph'],
        '{"version":"1.0","author":"system"}'
    ),
    (
        'query_graph',
        'Executes a graph query to find patterns and connections',
        '{"type":"object","properties":{"pattern":{"type":"string","description":"Graph pattern to match"},"depth":{"type":"number","description":"Traversal depth","default":3}},"required":["pattern"]}',
        'knowledge_graph',
        ARRAY['query', 'graph', 'traverse'],
        '{"version":"1.0","author":"system"}'
    ),
    (
        'execute_workflow',
        'Executes a predefined workflow with given parameters',
        '{"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow identifier"},"parameters":{"type":"object","description":"Workflow parameters"}},"required":["workflow_id"]}',
        'workflow',
        ARRAY['workflow', 'execute', 'automation'],
        '{"version":"1.0","author":"system"}'
    )
ON CONFLICT DO NOTHING;

-- Verify setup
SELECT 'Database schema initialized successfully!' AS status;
SELECT COUNT(*) AS tool_count FROM tools WHERE deleted_at IS NULL;
