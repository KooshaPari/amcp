-- SmartCP Execution History Migration - Rollback
-- Drops all objects created by 000002_execution_history.up.sql

-- Drop policies
DROP POLICY IF EXISTS smartcp_execution_history_service_access ON smartcp_execution_history;
DROP POLICY IF EXISTS smartcp_execution_history_user_isolation ON smartcp_execution_history;

-- Drop indexes
DROP INDEX IF EXISTS idx_smartcp_execution_history_failures;
DROP INDEX IF EXISTS idx_smartcp_execution_history_success;
DROP INDEX IF EXISTS idx_smartcp_execution_history_code_hash;
DROP INDEX IF EXISTS idx_smartcp_execution_history_language;
DROP INDEX IF EXISTS idx_smartcp_execution_history_user_created;
DROP INDEX IF EXISTS idx_smartcp_execution_history_user_id;

-- Drop table
DROP TABLE IF EXISTS smartcp_execution_history;
