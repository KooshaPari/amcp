-- SmartCP User Memory Migration - Rollback
-- Drops all objects created by 000001_user_memory.up.sql

-- Drop policies first (must be done before disabling RLS)
DROP POLICY IF EXISTS smartcp_user_memory_service_access ON smartcp_user_memory;
DROP POLICY IF EXISTS smartcp_user_memory_user_isolation ON smartcp_user_memory;

-- Drop trigger
DROP TRIGGER IF EXISTS trigger_smartcp_user_memory_updated_at ON smartcp_user_memory;

-- Drop function
DROP FUNCTION IF EXISTS update_smartcp_user_memory_updated_at();

-- Drop indexes
DROP INDEX IF EXISTS idx_smartcp_user_memory_updated;
DROP INDEX IF EXISTS idx_smartcp_user_memory_expires;
DROP INDEX IF EXISTS idx_smartcp_user_memory_importance;
DROP INDEX IF EXISTS idx_smartcp_user_memory_scope;
DROP INDEX IF EXISTS idx_smartcp_user_memory_user_key;
DROP INDEX IF EXISTS idx_smartcp_user_memory_user_id;

-- Drop table
DROP TABLE IF EXISTS smartcp_user_memory;
