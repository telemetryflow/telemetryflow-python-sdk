"""Unit tests for version utilities."""

from telemetryflow.version import (
    __version__,
    full,
    info,
    platform_info,
    python_version,
    short,
)


class TestVersion:
    """Test suite for version functions."""

    def test_version_format(self) -> None:
        """Test version string format."""
        assert __version__ == "1.1.1"

    def test_short(self) -> None:
        """Test short version."""
        version = short()

        assert version == __version__

    def test_full(self) -> None:
        """Test full version with commit."""
        version = full()

        assert __version__ in version
        assert "(" in version
        assert ")" in version

    def test_python_version(self) -> None:
        """Test Python version string."""
        version = python_version()

        # Should be in format X.Y.Z
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_platform_info(self) -> None:
        """Test platform info string."""
        platform = platform_info()

        # Should be in format os/arch
        assert "/" in platform
        parts = platform.split("/")
        assert len(parts) == 2

    def test_info(self) -> None:
        """Test full info string."""
        info_str = info()

        assert "TelemetryFlow Python SDK" in info_str
        assert __version__ in info_str
        assert "Python:" in info_str
        assert "Platform:" in info_str
        assert "Git Commit:" in info_str
        assert "Git Branch:" in info_str
        assert "Build Time:" in info_str
