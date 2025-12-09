-- SmartCP Learning Patterns Migration
-- Phase 1.1: User-scoped learning system
-- Addresses KI-6: Learning System Global State

CREATE TABLE IF NOT EXISTS smartcp_learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,

    -- Pattern classification
    pattern_type TEXT NOT NULL CHECK (pattern_type IN (
        'code_style',       -- User's coding style preferences
        'error_resolution', -- Common error fixes
        'tool_usage',       -- Tool usage patterns
        'workflow',         -- Workflow patterns
        'preference',       -- General preferences
        'context',          -- Contextual patterns
        'custom'            -- User-defined patterns
    )),
    pattern_name TEXT NOT NULL,

    -- Pattern data
    pattern_data JSONB NOT NULL DEFAULT '{}',
    examples JSONB DEFAULT '[]',  -- Example instances of this pattern

    -- Learning metrics
    confidence FLOAT NOT NULL DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    usage_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,

    -- Decay and reinforcement
    decay_rate FLOAT NOT NULL DEFAULT 0.1 CHECK (decay_rate >= 0.0 AND decay_rate <= 1.0),
    last_reinforced_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,

    -- Unique constraint: one pattern name per user per type
    CONSTRAINT uq_learning_pattern UNIQUE (user_id, pattern_type, pattern_name)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_smartcp_learning_patterns_user_id
    ON smartcp_learning_patterns(user_id);

CREATE INDEX IF NOT EXISTS idx_smartcp_learning_patterns_user_type
    ON smartcp_learning_patterns(user_id, pattern_type);

CREATE INDEX IF NOT EXISTS idx_smartcp_learning_patterns_confidence
    ON smartcp_learning_patterns(user_id, confidence DESC);

CREATE INDEX IF NOT EXISTS idx_smartcp_learning_patterns_usage
    ON smartcp_learning_patterns(user_id, usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_smartcp_learning_patterns_updated
    ON smartcp_learning_patterns(updated_at DESC);

-- Partial index for high-confidence patterns
CREATE INDEX IF NOT EXISTS idx_smartcp_learning_patterns_high_confidence
    ON smartcp_learning_patterns(user_id, pattern_type)
    WHERE confidence >= 0.7;

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_smartcp_learning_patterns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS trigger_smartcp_learning_patterns_updated_at ON smartcp_learning_patterns;
CREATE TRIGGER trigger_smartcp_learning_patterns_updated_at
    BEFORE UPDATE ON smartcp_learning_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_smartcp_learning_patterns_updated_at();

-- Function to calculate success rate
CREATE OR REPLACE FUNCTION smartcp_learning_pattern_success_rate(
    p_usage_count INTEGER,
    p_success_count INTEGER
)
RETURNS FLOAT AS $$
BEGIN
    IF p_usage_count = 0 THEN
        RETURN 0.0;
    END IF;
    RETURN p_success_count::FLOAT / p_usage_count::FLOAT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Row Level Security for user isolation
ALTER TABLE smartcp_learning_patterns ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own learning patterns
DROP POLICY IF EXISTS smartcp_learning_patterns_user_isolation ON smartcp_learning_patterns;
CREATE POLICY smartcp_learning_patterns_user_isolation ON smartcp_learning_patterns
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Service role can access all entries
DROP POLICY IF EXISTS smartcp_learning_patterns_service_access ON smartcp_learning_patterns;
CREATE POLICY smartcp_learning_patterns_service_access ON smartcp_learning_patterns
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Comment on table and columns
COMMENT ON TABLE smartcp_learning_patterns IS 'SmartCP user-scoped learning patterns for adaptive behavior';
COMMENT ON COLUMN smartcp_learning_patterns.user_id IS 'User ID from auth token';
COMMENT ON COLUMN smartcp_learning_patterns.pattern_type IS 'Category of learning pattern';
COMMENT ON COLUMN smartcp_learning_patterns.pattern_name IS 'Unique name for this pattern within type';
COMMENT ON COLUMN smartcp_learning_patterns.pattern_data IS 'JSONB containing pattern specifics';
COMMENT ON COLUMN smartcp_learning_patterns.examples IS 'Array of example instances';
COMMENT ON COLUMN smartcp_learning_patterns.confidence IS 'Confidence score (0.0-1.0) based on reinforcement';
COMMENT ON COLUMN smartcp_learning_patterns.decay_rate IS 'How quickly pattern confidence decays without use';
COMMENT ON COLUMN smartcp_learning_patterns.last_reinforced_at IS 'Last time pattern was positively reinforced';
