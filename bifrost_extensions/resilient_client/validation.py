"""Message validation for Bifrost client."""

from typing import Dict, List

from bifrost_extensions.models import Message
from bifrost_extensions.exceptions import ValidationError
from bifrost_extensions.security.validation import InputValidator


def validate_messages(
    messages: List[Message] | List[Dict[str, str]]
) -> List[Message]:
    """Validate and sanitize messages.

    Args:
        messages: Raw messages to validate

    Returns:
        List of validated Message objects

    Raises:
        ValidationError: If message validation fails
    """
    validated = []

    for msg in messages:
        if isinstance(msg, dict):
            # Sanitize content
            content = InputValidator.sanitize_string(
                msg.get("content", ""),
                max_length=100000,
            )

            # Validate role
            role = msg.get("role", "user")
            if role not in ["user", "assistant", "system"]:
                raise ValidationError(
                    f"Invalid role: {role}",
                    details={"allowed": ["user", "assistant", "system"]},
                )

            validated.append(Message(role=role, content=content))
        else:
            validated.append(msg)

    return validated
