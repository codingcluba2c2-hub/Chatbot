import re
from typing import Tuple

class InputGuardrail:
    RESTRICTED_PATTERNS = [
        r"(?i)ignore previous instructions",
        r"(?i)system prompt",
        r"(?i)drop table",
        r"(?i)SELECT .* FROM",
    ]

    @staticmethod
    def validate(user_message: str) -> Tuple[bool, str]:
        for pattern in InputGuardrail.RESTRICTED_PATTERNS:
            if re.search(pattern, user_message):
                return False, f"Prompt injection or restricted phrase detected."
                
        return True, "Passed"
