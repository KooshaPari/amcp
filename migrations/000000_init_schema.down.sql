-- Rollback initial schema

BEGIN;

-- Drop triggers
DROP TRIGGER IF EXISTS update_mcp_servers_updated_at ON mcp_servers;
DROP TRIGGER IF EXISTS update_tools_updated_at ON tools_registry;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_workspaces_updated_at ON workspaces;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables in reverse order (respecting foreign keys)
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS mcp_servers;
DROP TABLE IF EXISTS tools_registry;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS workspaces;

COMMIT;
