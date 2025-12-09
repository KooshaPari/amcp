"""Error types for state management."""


class StateError(Exception):
    """Base error for state operations."""

    def __init__(self, message: str, code: str = "STATE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class StateNotFoundError(StateError):
    """State key not found."""

    def __init__(self, key: str, user_id: str):
        super().__init__(f"State key '{key}' not found for user {user_id}", "NOT_FOUND")


class BifrostStateError(StateError):
    """Bifrost GraphQL error during state operation."""

    def __init__(self, message: str, operation: str, original_error: Exception):
        super().__init__(f"Bifrost {operation} failed: {message}", "BIFROST_ERROR")
        self.original_error = original_error
