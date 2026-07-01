"""PII Masker — detect and mask personally identifiable information in logs and data."""

from __future__ import annotations

import re
from typing import Any

import structlog

logger = structlog.get_logger()


class PIIMasker:
    """Detects and masks PII in strings and structured data.

    Used in logging, conversation exports, and analytics to prevent
    accidental PII exposure.

    Supports: emails, phone numbers, credit cards, SSNs, IP addresses,
    and custom patterns.

    Usage:
        masker = PIIMasker()
        masked = masker.mask_string("Contact john@example.com or call 555-123-4567")
        # "Contact j***@***.com or call ***-***-4567"
    """

    # Default PII patterns
    PATTERNS: list[tuple[str, str, str]] = [
        # (name, regex_pattern, replacement_function_name)
        ("email", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "_mask_email"),
        ("phone", r"\b(?:\+?1[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}\b", "_mask_phone"),
        ("credit_card", r"\b(?:[0-9]{4}[-\s]?){3}[0-9]{4}\b", "_mask_credit_card"),
        ("ssn", r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b", "_mask_ssn"),
        ("ipv4", r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "_mask_ip"),
    ]

    # Fields that are always masked in structured data
    SENSITIVE_FIELDS: set[str] = {
        "password", "secret", "token", "api_key", "access_token",
        "refresh_token", "private_key", "ssn", "credit_card",
        "card_number", "cvv", "authorization",
    }

    def __init__(self, custom_patterns: list[tuple[str, str, str]] | None = None) -> None:
        self._patterns = self.PATTERNS.copy()
        if custom_patterns:
            self._patterns.extend(custom_patterns)
        self._compiled = [(name, re.compile(pattern)) for name, pattern, _ in self._patterns]

    def mask_string(self, text: str) -> str:
        """Mask all PII patterns found in a string."""
        result = text
        for name, pattern, mask_fn_name in self.PATTERNS:
            compiled = re.compile(pattern)
            mask_fn = getattr(self, mask_fn_name, self._mask_generic)
            result = compiled.sub(lambda m, fn=mask_fn: fn(m.group()), result)
        return result

    def mask_dict(self, data: dict[str, Any], depth: int = 0, max_depth: int = 10) -> dict[str, Any]:
        """Recursively mask PII in a dictionary."""
        if depth > max_depth:
            return data

        masked: dict[str, Any] = {}
        for key, value in data.items():
            # Check if the field name itself is sensitive
            if key.lower() in self.SENSITIVE_FIELDS:
                masked[key] = "***REDACTED***"
            elif isinstance(value, str):
                masked[key] = self.mask_string(value)
            elif isinstance(value, dict):
                masked[key] = self.mask_dict(value, depth + 1, max_depth)
            elif isinstance(value, list):
                masked[key] = [
                    self.mask_dict(item, depth + 1, max_depth) if isinstance(item, dict)
                    else self.mask_string(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                masked[key] = value
        return masked

    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask email: j***@***.com"""
        parts = email.split("@")
        if len(parts) == 2:
            local, domain = parts
            domain_parts = domain.split(".")
            return f"{local[0]}***@***.{domain_parts[-1]}"
        return "***@***.***"

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Mask phone: keep last 4 digits."""
        digits = re.sub(r"[^\d]", "", phone)
        if len(digits) >= 4:
            return f"***-***-{digits[-4:]}"
        return "***"

    @staticmethod
    def _mask_credit_card(card: str) -> str:
        """Mask credit card: keep last 4 digits."""
        digits = re.sub(r"[^\d]", "", card)
        if len(digits) >= 4:
            return f"****-****-****-{digits[-4:]}"
        return "****-****-****-****"

    @staticmethod
    def _mask_ssn(ssn: str) -> str:
        """Mask SSN: ***-**-last4."""
        parts = ssn.split("-")
        if len(parts) == 3:
            return f"***-**-{parts[2]}"
        return "***-**-****"

    @staticmethod
    def _mask_ip(ip: str) -> str:
        """Mask IP address: keep first octet."""
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.***.***.***.***"
        return "***.***.***.***"

    @staticmethod
    def _mask_generic(value: str) -> str:
        """Generic masking: replace with asterisks."""
        if len(value) <= 4:
            return "****"
        return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"


# Global masker instance
pii_masker = PIIMasker()
