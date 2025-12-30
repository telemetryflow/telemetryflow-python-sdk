"""Unit tests for Credentials value object."""

import pytest

from telemetryflow.domain.credentials import (
    KEY_ID_PREFIX,
    KEY_SECRET_PREFIX,
    Credentials,
    CredentialsError,
)


class TestCredentials:
    """Test suite for Credentials class."""

    def test_create_valid_credentials(self) -> None:
        """Test creating valid credentials."""
        creds = Credentials.create("tfk_test_key_id", "tfs_test_key_secret")

        assert creds.key_id == "tfk_test_key_id"
        assert creds.key_secret == "tfs_test_key_secret"

    def test_create_credentials_using_dataclass(self) -> None:
        """Test creating credentials using dataclass constructor."""
        creds = Credentials(key_id="tfk_abc123", key_secret="tfs_xyz789")

        assert creds.key_id == "tfk_abc123"
        assert creds.key_secret == "tfs_xyz789"

    def test_empty_key_id_raises_error(self) -> None:
        """Test that empty key ID raises CredentialsError."""
        with pytest.raises(CredentialsError, match="API key ID is required"):
            Credentials.create("", "tfs_secret")

    def test_empty_key_secret_raises_error(self) -> None:
        """Test that empty key secret raises CredentialsError."""
        with pytest.raises(CredentialsError, match="API key secret is required"):
            Credentials.create("tfk_key", "")

    def test_invalid_key_id_prefix_raises_error(self) -> None:
        """Test that invalid key ID prefix raises CredentialsError."""
        with pytest.raises(CredentialsError, match=f"must start with '{KEY_ID_PREFIX}'"):
            Credentials.create("invalid_key_id", "tfs_secret")

    def test_invalid_key_secret_prefix_raises_error(self) -> None:
        """Test that invalid key secret prefix raises CredentialsError."""
        with pytest.raises(CredentialsError, match=f"must start with '{KEY_SECRET_PREFIX}'"):
            Credentials.create("tfk_key", "invalid_secret")

    def test_authorization_header(self) -> None:
        """Test authorization header generation."""
        creds = Credentials.create("tfk_key123", "tfs_secret456")

        header = creds.authorization_header()

        assert header == "Bearer tfk_key123:tfs_secret456"

    def test_auth_headers(self) -> None:
        """Test auth headers generation."""
        creds = Credentials.create("tfk_key123", "tfs_secret456")

        headers = creds.auth_headers()

        assert headers["Authorization"] == "Bearer tfk_key123:tfs_secret456"
        assert headers["X-TelemetryFlow-Key-ID"] == "tfk_key123"
        assert headers["X-TelemetryFlow-Key-Secret"] == "tfs_secret456"

    def test_equals_same_credentials(self) -> None:
        """Test equality with same credentials."""
        creds1 = Credentials.create("tfk_key", "tfs_secret")
        creds2 = Credentials.create("tfk_key", "tfs_secret")

        assert creds1.equals(creds2)
        assert creds2.equals(creds1)

    def test_equals_different_credentials(self) -> None:
        """Test equality with different credentials."""
        creds1 = Credentials.create("tfk_key1", "tfs_secret1")
        creds2 = Credentials.create("tfk_key2", "tfs_secret2")

        assert not creds1.equals(creds2)
        assert not creds2.equals(creds1)

    def test_equals_none(self) -> None:
        """Test equality with None."""
        creds = Credentials.create("tfk_key", "tfs_secret")

        assert not creds.equals(None)

    def test_str_hides_secret(self) -> None:
        """Test that string representation hides the secret."""
        creds = Credentials.create("tfk_key123", "tfs_verylongsecret123")

        str_repr = str(creds)

        assert "tfk_key123" in str_repr
        assert "verylongsecret" not in str_repr
        assert "tfs_very..." in str_repr or "..." in str_repr

    def test_immutability(self) -> None:
        """Test that credentials are immutable (frozen dataclass)."""
        creds = Credentials.create("tfk_key", "tfs_secret")

        with pytest.raises(AttributeError):
            creds.key_id = "tfk_new_key"  # type: ignore

    def test_class_constants(self) -> None:
        """Test class-level constants."""
        assert Credentials.KEY_ID_PREFIX == "tfk_"
        assert Credentials.KEY_SECRET_PREFIX == "tfs_"
