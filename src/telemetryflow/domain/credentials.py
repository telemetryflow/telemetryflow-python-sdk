"""Credentials value object for TelemetryFlow authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

KEY_ID_PREFIX = "tfk_"
KEY_SECRET_PREFIX = "tfs_"


class CredentialsError(Exception):
    """Exception raised for credential validation errors."""

    pass


@dataclass(frozen=True)
class Credentials:
    """
    Immutable value object representing TelemetryFlow API credentials.

    Credentials consist of a key ID (prefixed with 'tfk_') and a key secret
    (prefixed with 'tfs_'). This class validates the format and provides
    methods for generating authentication headers.

    Attributes:
        key_id: The API key ID (must start with 'tfk_')
        key_secret: The API key secret (must start with 'tfs_')
    """

    key_id: str
    key_secret: str

    # Class-level constants
    KEY_ID_PREFIX: ClassVar[str] = KEY_ID_PREFIX
    KEY_SECRET_PREFIX: ClassVar[str] = KEY_SECRET_PREFIX

    def __post_init__(self) -> None:
        """Validate credentials after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the credential format."""
        if not self.key_id:
            raise CredentialsError("API key ID is required")
        if not self.key_secret:
            raise CredentialsError("API key secret is required")
        if not self.key_id.startswith(KEY_ID_PREFIX):
            raise CredentialsError(f"API key ID must start with '{KEY_ID_PREFIX}'")
        if not self.key_secret.startswith(KEY_SECRET_PREFIX):
            raise CredentialsError(f"API key secret must start with '{KEY_SECRET_PREFIX}'")

    def authorization_header(self) -> str:
        """
        Generate the Authorization header value.

        Returns:
            The Bearer token string in format "Bearer {key_id}:{key_secret}"
        """
        return f"Bearer {self.key_id}:{self.key_secret}"

    def auth_headers(self) -> dict[str, str]:
        """
        Generate all authentication headers for TelemetryFlow API.

        Returns:
            Dictionary of header names to values
        """
        return {
            "Authorization": self.authorization_header(),
            "X-TelemetryFlow-Key-ID": self.key_id,
            "X-TelemetryFlow-Key-Secret": self.key_secret,
        }

    def equals(self, other: Credentials | None) -> bool:
        """
        Check equality with another Credentials instance.

        Args:
            other: Another Credentials instance to compare with

        Returns:
            True if both credentials are equal
        """
        if other is None:
            return False
        return self.key_id == other.key_id and self.key_secret == other.key_secret

    def __str__(self) -> str:
        """Return a safe string representation (hides secret)."""
        secret_preview = self.key_secret[:8] + "..." if len(self.key_secret) > 8 else "***"
        return f"Credentials(key_id={self.key_id}, key_secret={secret_preview})"

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return self.__str__()

    @classmethod
    def create(cls, key_id: str, key_secret: str) -> Credentials:
        """
        Factory method to create Credentials with validation.

        Args:
            key_id: The API key ID
            key_secret: The API key secret

        Returns:
            A new Credentials instance

        Raises:
            CredentialsError: If validation fails
        """
        return cls(key_id=key_id, key_secret=key_secret)
