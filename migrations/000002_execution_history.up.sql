-- SmartCP Execution History Migration
-- Phase 1.1: User-scoped code execution history
-- Addresses KI-5: Code Executor Without User Sandbox

CREATE TABLE IF NOT EXISTS smartcp_execution_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,

    -- Execution details
    language TEXT NOT NULL CHECK (language IN ('python', 'typescript', 'bash', 'go', 'rust')),
    code_hash TEXT NOT NULL,
    code_snippet TEXT,  -- First 500 chars for debugging (not full code for security)

    -- Results
    success BOOLEAN NOT NULL,
    output TEXT,
    error TEXT,
    exit_code INTEGER,

    -- Performance metrics
    execution_time_ms INTEGER NOT NULL DEFAULT 0,
    memory_used_mb FLOAT,
    cpu_time_ms INTEGER,

    -- Sandbox info
    sandbox_id TEXT,  -- Reference to sandbox directory

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_smartcp_execution_history_user_id
    ON smartcp_execution_history(user_id);

CREATE INDEX IF NOT EXISTS idx_smartcp_execution_history_user_created
    ON smartcp_execution_history(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_smartcp_execution_history_language
    ON smartcp_execution_history(user_id, language);

CREATE INDEX IF NOT EXISTS idx_smartcp_execution_history_code_hash
    ON smartcp_execution_history(user_id, code_hash);

CREATE INDEX IF NOT EXISTS idx_smartcp_execution_history_success
    ON smartcp_execution_history(user_id, success);

-- Partial index for failed executions (for debugging)
CREATE INDEX IF NOT EXISTS idx_smartcp_execution_history_failures
    ON smartcp_execution_history(user_id, created_at DESC)
    WHERE success = false;

-- Row Level Security for user isolation
ALTER TABLE smartcp_execution_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own execution history
DROP POLICY IF EXISTS smartcp_execution_history_user_isolation ON smartcp_execution_history;
CREATE POLICY smartcp_execution_history_user_isolation ON smartcp_execution_history
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Service role can access all entries
DROP POLICY IF EXISTS smartcp_execution_history_service_access ON smartcp_execution_history;
CREATE POLICY smartcp_execution_history_service_access ON smartcp_execution_history
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Comment on table and columns
COMMENT ON TABLE smartcp_execution_history IS 'SmartCP code execution history with user isolation';
COMMENT ON COLUMN smartcp_execution_history.user_id IS 'User ID from auth token';
COMMENT ON COLUMN smartcp_execution_history.language IS 'Programming language of executed code';
COMMENT ON COLUMN smartcp_execution_history.code_hash IS 'SHA-256 hash of code for deduplication';
COMMENT ON COLUMN smartcp_execution_history.code_snippet IS 'First 500 chars of code for debugging';
COMMENT ON COLUMN smartcp_execution_history.sandbox_id IS 'Reference to user sandbox directory';
COMMENT ON COLUMN smartcp_execution_history.execution_time_ms IS 'Total execution time in milliseconds';
COMMENT ON COLUMN smartcp_execution_history.memory_used_mb IS 'Peak memory usage in megabytes';
