-- SmartCP User Memory Migration
-- Phase 1.1: User-scoped state management for HTTP stateless transport
-- Replaces session-based SQLite storage with user-scoped Supabase/PostgreSQL

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User memory table: Stores hierarchical memory entries keyed by user_id
-- Addresses KI-1: Session-Based Memory System → User-Scoped Memory
CREATE TABLE IF NOT EXISTS smartcp_user_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    scope TEXT NOT NULL DEFAULT 'user' CHECK (scope IN ('user', 'workspace', 'global')),
    importance FLOAT NOT NULL DEFAULT 0.5 CHECK (importance >= 0.0 AND importance <= 1.0),
    access_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    -- Unique constraint: one key per user per scope
    CONSTRAINT uq_user_memory_key UNIQUE (user_id, key, scope)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_smartcp_user_memory_user_id
    ON smartcp_user_memory(user_id);

CREATE INDEX IF NOT EXISTS idx_smartcp_user_memory_user_key
    ON smartcp_user_memory(user_id, key);

CREATE INDEX IF NOT EXISTS idx_smartcp_user_memory_scope
    ON smartcp_user_memory(user_id, scope);

CREATE INDEX IF NOT EXISTS idx_smartcp_user_memory_importance
    ON smartcp_user_memory(user_id, importance DESC);

CREATE INDEX IF NOT EXISTS idx_smartcp_user_memory_expires
    ON smartcp_user_memory(expires_at)
    WHERE expires_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_smartcp_user_memory_updated
    ON smartcp_user_memory(updated_at DESC);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_smartcp_user_memory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS trigger_smartcp_user_memory_updated_at ON smartcp_user_memory;
CREATE TRIGGER trigger_smartcp_user_memory_updated_at
    BEFORE UPDATE ON smartcp_user_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_smartcp_user_memory_updated_at();

-- Row Level Security (RLS) for user isolation
ALTER TABLE smartcp_user_memory ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own memory entries
DROP POLICY IF EXISTS smartcp_user_memory_user_isolation ON smartcp_user_memory;
CREATE POLICY smartcp_user_memory_user_isolation ON smartcp_user_memory
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Service role can access all entries (for admin/migration purposes)
DROP POLICY IF EXISTS smartcp_user_memory_service_access ON smartcp_user_memory;
CREATE POLICY smartcp_user_memory_service_access ON smartcp_user_memory
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Comment on table and columns for documentation
COMMENT ON TABLE smartcp_user_memory IS 'SmartCP hierarchical memory storage with user-scoped isolation';
COMMENT ON COLUMN smartcp_user_memory.user_id IS 'User ID from auth token (replaces session_id)';
COMMENT ON COLUMN smartcp_user_memory.key IS 'Memory entry key (unique per user/scope)';
COMMENT ON COLUMN smartcp_user_memory.value IS 'Memory entry value as JSONB';
COMMENT ON COLUMN smartcp_user_memory.scope IS 'Memory scope: user (personal), workspace (shared), global (system)';
COMMENT ON COLUMN smartcp_user_memory.importance IS 'Memory importance score for prioritization (0.0-1.0)';
COMMENT ON COLUMN smartcp_user_memory.access_count IS 'Number of times this entry has been accessed';
COMMENT ON COLUMN smartcp_user_memory.expires_at IS 'Optional TTL expiration timestamp';
