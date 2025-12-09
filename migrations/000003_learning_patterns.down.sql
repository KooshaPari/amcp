-- SmartCP Learning Patterns Migration - Rollback
-- Drops all objects created by 000003_learning_patterns.up.sql

-- Drop policies
DROP POLICY IF EXISTS smartcp_learning_patterns_service_access ON smartcp_learning_patterns;
DROP POLICY IF EXISTS smartcp_learning_patterns_user_isolation ON smartcp_learning_patterns;

-- Drop trigger
DROP TRIGGER IF EXISTS trigger_smartcp_learning_patterns_updated_at ON smartcp_learning_patterns;

-- Drop functions
DROP FUNCTION IF EXISTS update_smartcp_learning_patterns_updated_at();
DROP FUNCTION IF EXISTS smartcp_learning_pattern_success_rate(INTEGER, INTEGER);

-- Drop indexes
DROP INDEX IF EXISTS idx_smartcp_learning_patterns_high_confidence;
DROP INDEX IF EXISTS idx_smartcp_learning_patterns_updated;
DROP INDEX IF EXISTS idx_smartcp_learning_patterns_usage;
DROP INDEX IF EXISTS idx_smartcp_learning_patterns_confidence;
DROP INDEX IF EXISTS idx_smartcp_learning_patterns_user_type;
DROP INDEX IF EXISTS idx_smartcp_learning_patterns_user_id;

-- Drop table
DROP TABLE IF EXISTS smartcp_learning_patterns;
