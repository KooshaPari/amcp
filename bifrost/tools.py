"""SmartCP Tool Definitions for Bifrost Integration.

This module contains all tool schema definitions for SmartCP.
Tools are organized by category: execution, memory, and state.

Tool definitions are structured as dictionaries to avoid circular imports.
The registry module converts these to ToolSchema objects.
"""

# Execution Tools
EXECUTE_CODE_TOOL_DEF = {
    "name": "execute_code",
    "description": (
        "Execute code in a sandboxed environment. "
        "Supports Python with user-isolated variable namespace. "
        "Variables persist across calls within the same user session."
    ),
    "category": "execution",
    "tags": ["code", "python", "sandbox", "compute"],
    "returns_description": (
        "Dictionary with execution_id, status, output, error, result, and variables"
    ),
    "parameters": [
        {
            "name": "code",
            "type": "string",
            "description": "The code to execute",
            "required": True,
        },
        {
            "name": "language",
            "type": "string",
            "description": "Programming language (currently only 'python' supported)",
            "required": False,
            "default": "python",
            "enum": ["python"],
        },
        {
            "name": "timeout",
            "type": "integer",
            "description": "Maximum execution time in seconds (1-300)",
            "required": False,
            "default": 30,
        },
        {
            "name": "context",
            "type": "object",
            "description": "Optional context variables to inject",
            "required": False,
        },
    ],
}

GET_VARIABLES_TOOL_DEF = {
    "name": "get_variables",
    "description": (
        "Get all variables in the current execution namespace. "
        "Returns user-defined variables from previous execute_code calls."
    ),
    "category": "execution",
    "tags": ["code", "variables", "state"],
    "returns_description": "Dictionary with variables (dict) and count (int)",
    "parameters": [],
}

SET_VARIABLE_TOOL_DEF = {
    "name": "set_variable",
    "description": (
        "Set a variable in the execution namespace. "
        "The variable will be available in subsequent execute_code calls."
    ),
    "category": "execution",
    "tags": ["code", "variables", "state"],
    "returns_description": "Dictionary with success (bool) and name (str)",
    "parameters": [
        {
            "name": "name",
            "type": "string",
            "description": "Variable name (must be a valid Python identifier)",
            "required": True,
        },
        {
            "name": "value",
            "type": "object",
            "description": "Variable value (must be JSON-serializable)",
            "required": True,
        },
    ],
}

DELETE_VARIABLE_TOOL_DEF = {
    "name": "delete_variable",
    "description": "Delete a variable from the execution namespace.",
    "category": "execution",
    "tags": ["code", "variables", "state"],
    "returns_description": "Dictionary with success (bool) and name (str)",
    "parameters": [
        {
            "name": "name",
            "type": "string",
            "description": "Variable name to delete",
            "required": True,
        },
    ],
}

CLEAR_VARIABLES_TOOL_DEF = {
    "name": "clear_variables",
    "description": "Clear all variables from the execution namespace.",
    "category": "execution",
    "tags": ["code", "variables", "state"],
    "returns_description": "Dictionary with success (bool) and count (int)",
    "parameters": [],
}

# Memory Tools
STORE_MEMORY_TOOL_DEF = {
    "name": "store_memory",
    "description": (
        "Store a value in user memory. Memory is isolated per user and "
        "persists across requests. Different types have different lifetimes: "
        "working (1hr TTL), persistent (never expires), context."
    ),
    "category": "memory",
    "tags": ["memory", "storage", "state", "persistence"],
    "returns_description": "Dictionary with success, key, memory_type, and expires_at",
    "parameters": [
        {
            "name": "key",
            "type": "string",
            "description": "Memory key (unique within memory type)",
            "required": True,
        },
        {
            "name": "value",
            "type": "object",
            "description": "Value to store (must be JSON-serializable)",
            "required": True,
        },
        {
            "name": "memory_type",
            "type": "string",
            "description": "Type of memory",
            "required": False,
            "default": "working",
            "enum": ["working", "persistent", "context"],
        },
        {
            "name": "ttl",
            "type": "integer",
            "description": "Optional time-to-live in seconds (overrides default)",
            "required": False,
        },
    ],
}

RETRIEVE_MEMORY_TOOL_DEF = {
    "name": "retrieve_memory",
    "description": "Retrieve a value from user memory.",
    "category": "memory",
    "tags": ["memory", "storage", "state", "retrieval"],
    "returns_description": "Dictionary with found, key, value, and memory_type",
    "parameters": [
        {
            "name": "key",
            "type": "string",
            "description": "Memory key to retrieve",
            "required": True,
        },
        {
            "name": "memory_type",
            "type": "string",
            "description": "Type of memory to search",
            "required": False,
            "default": "working",
            "enum": ["working", "persistent", "context"],
        },
    ],
}

DELETE_MEMORY_TOOL_DEF = {
    "name": "delete_memory",
    "description": "Delete a value from user memory.",
    "category": "memory",
    "tags": ["memory", "storage", "state"],
    "returns_description": "Dictionary with success, key, and memory_type",
    "parameters": [
        {
            "name": "key",
            "type": "string",
            "description": "Memory key to delete",
            "required": True,
        },
        {
            "name": "memory_type",
            "type": "string",
            "description": "Type of memory",
            "required": False,
            "default": "working",
            "enum": ["working", "persistent", "context"],
        },
    ],
}

LIST_MEMORY_KEYS_TOOL_DEF = {
    "name": "list_memory_keys",
    "description": "List all memory keys for the user.",
    "category": "memory",
    "tags": ["memory", "storage", "state", "listing"],
    "returns_description": "Dictionary with keys (list), count, and memory_type",
    "parameters": [
        {
            "name": "memory_type",
            "type": "string",
            "description": "Optional filter by type (None for all types)",
            "required": False,
            "enum": ["working", "persistent", "context"],
        },
    ],
}

CLEAR_MEMORY_TOOL_DEF = {
    "name": "clear_memory",
    "description": "Clear user memory. WARNING: Deletes all memory of the specified type.",
    "category": "memory",
    "tags": ["memory", "storage", "state", "delete"],
    "returns_description": "Dictionary with success, count, and memory_type",
    "parameters": [
        {
            "name": "memory_type",
            "type": "string",
            "description": "Type to clear (None to clear all memory)",
            "required": False,
            "enum": ["working", "persistent", "context"],
        },
    ],
}

GET_MEMORY_STATS_TOOL_DEF = {
    "name": "get_memory_stats",
    "description": "Get memory usage statistics.",
    "category": "memory",
    "tags": ["memory", "stats", "metrics"],
    "returns_description": "Dictionary with total_items and counts per memory type",
    "parameters": [],
}

# State Tools
STATE_GET_TOOL_DEF = {
    "name": "state_get",
    "description": (
        "Get a raw state value. Low-level state access. "
        "For most use cases, prefer retrieve_memory."
    ),
    "category": "state",
    "tags": ["state", "storage", "low-level"],
    "returns_description": "Dictionary with found, key, and value",
    "parameters": [
        {
            "name": "key",
            "type": "string",
            "description": "State key",
            "required": True,
        },
        {
            "name": "default",
            "type": "object",
            "description": "Default value if not found",
            "required": False,
        },
    ],
}

STATE_SET_TOOL_DEF = {
    "name": "state_set",
    "description": (
        "Set a raw state value. Low-level state access. "
        "For most use cases, prefer store_memory."
    ),
    "category": "state",
    "tags": ["state", "storage", "low-level"],
    "returns_description": "Dictionary with success and key",
    "parameters": [
        {
            "name": "key",
            "type": "string",
            "description": "State key",
            "required": True,
        },
        {
            "name": "value",
            "type": "object",
            "description": "Value to store (must be JSON-serializable)",
            "required": True,
        },
        {
            "name": "ttl",
            "type": "integer",
            "description": "Optional time-to-live in seconds",
            "required": False,
        },
    ],
}

STATE_DELETE_TOOL_DEF = {
    "name": "state_delete",
    "description": "Delete a raw state value.",
    "category": "state",
    "tags": ["state", "storage", "low-level"],
    "returns_description": "Dictionary with success and key",
    "parameters": [
        {
            "name": "key",
            "type": "string",
            "description": "State key to delete",
            "required": True,
        },
    ],
}

STATE_EXISTS_TOOL_DEF = {
    "name": "state_exists",
    "description": "Check if a state key exists.",
    "category": "state",
    "tags": ["state", "storage", "low-level"],
    "returns_description": "Dictionary with exists and key",
    "parameters": [
        {
            "name": "key",
            "type": "string",
            "description": "State key to check",
            "required": True,
        },
    ],
}

STATE_LIST_KEYS_TOOL_DEF = {
    "name": "state_list_keys",
    "description": "List all state keys.",
    "category": "state",
    "tags": ["state", "storage", "low-level", "listing"],
    "returns_description": "Dictionary with keys, count, and prefix",
    "parameters": [
        {
            "name": "prefix",
            "type": "string",
            "description": "Optional prefix filter",
            "required": False,
        },
    ],
}

STATE_CLEAR_TOOL_DEF = {
    "name": "state_clear",
    "description": "Clear state keys. WARNING: Deletes all matching state.",
    "category": "state",
    "tags": ["state", "storage", "low-level", "delete"],
    "returns_description": "Dictionary with success, count, and prefix",
    "parameters": [
        {
            "name": "prefix",
            "type": "string",
            "description": "Optional prefix to limit deletion (None clears all)",
            "required": False,
        },
    ],
}

# Export all tool definitions
ALL_TOOL_DEFS = [
    EXECUTE_CODE_TOOL_DEF,
    GET_VARIABLES_TOOL_DEF,
    SET_VARIABLE_TOOL_DEF,
    DELETE_VARIABLE_TOOL_DEF,
    CLEAR_VARIABLES_TOOL_DEF,
    STORE_MEMORY_TOOL_DEF,
    RETRIEVE_MEMORY_TOOL_DEF,
    DELETE_MEMORY_TOOL_DEF,
    LIST_MEMORY_KEYS_TOOL_DEF,
    CLEAR_MEMORY_TOOL_DEF,
    GET_MEMORY_STATS_TOOL_DEF,
    STATE_GET_TOOL_DEF,
    STATE_SET_TOOL_DEF,
    STATE_DELETE_TOOL_DEF,
    STATE_EXISTS_TOOL_DEF,
    STATE_LIST_KEYS_TOOL_DEF,
    STATE_CLEAR_TOOL_DEF,
]
