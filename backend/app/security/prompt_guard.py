import re
from typing import Tuple

INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?(previous|prior|above)\s+instructions',
    r'disregard\s+(all\s+)?(previous|prior)\s+instructions',
    r'reveal\s+(the\s+)?(system\s+prompt|api\s+key|password|credential|secret)',
    r'you\s+are\s+now\s+in\s+developer\s+mode',
    r'bypass\s+all\s+(security|safety|guidelines)',
    r'dan\s+mode\s+enabled',
    r'system\s*:\s*override',
    r'show\s+(me\s+)?(system\s+instruction|internal\s+config|env\s+file)',
    r'dump\s+database\s+credentials'
]

class PromptGuard:
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Strips or escapes potential jailbreak or prompt override delimiters.
        """
        if not text:
            return ""
        # Neutralize markdown system impersonation blocks like <system>, ```system
        cleaned = re.sub(r'<\s*system[^>]*>.*?<\s*/\s*system\s*>', '', text, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'```system.*?```', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def check_injection(text: str) -> Tuple[bool, str]:
        """
        Checks whether text contains adversarial prompt injection patterns.
        Returns (is_suspicious: bool, reason: str).
        """
        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True, "Potential prompt injection or instruction override detected."
        return False, ""

    @staticmethod
    def wrap_context_safely(document_name: str, page: int, content: str) -> str:
        """
        Encapsulates document content inside an unprivileged untrusted-data boundary.
        """
        sanitized = PromptGuard.sanitize_text(content)
        # Explicit data framing so the LLM treats it purely as inert knowledge
        return f"=== BEGIN UNTRUSTED COMPANY DOCUMENT: {document_name} (Page {page}) ===\n{sanitized}\n=== END UNTRUSTED COMPANY DOCUMENT ==="
