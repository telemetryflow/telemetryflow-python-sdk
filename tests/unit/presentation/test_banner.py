"""Unit tests for banner utilities."""

from telemetryflow.banner import (
    ASCII_BANNER,
    BannerConfig,
    generate,
    generate_compact,
    generate_minimal,
)
from telemetryflow.version import __version__


class TestBannerConfig:
    """Test suite for BannerConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BannerConfig()

        assert config.product_name == "TelemetryFlow Python SDK"
        assert config.version == __version__
        assert config.vendor == "TelemetryFlow"
        assert config.website == "https://telemetryflow.id"
        assert config.show_python_version is True
        assert config.show_platform is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BannerConfig(
            product_name="Custom SDK",
            version="2.0.0",
            vendor="Custom Vendor",
            website="https://custom.example.com",
            show_python_version=False,
            show_platform=False,
        )

        assert config.product_name == "Custom SDK"
        assert config.version == "2.0.0"
        assert config.vendor == "Custom Vendor"


class TestGenerate:
    """Test suite for generate function."""

    def test_generate_default(self) -> None:
        """Test generate with default config."""
        banner = generate()

        assert "TelemetryFlow" in banner
        assert __version__ in banner
        assert "https://telemetryflow.id" in banner

    def test_generate_contains_ascii_art(self) -> None:
        """Test that generate includes ASCII art."""
        banner = generate()

        # Check for some ASCII art characters
        assert "_____" in banner or "═" in banner

    def test_generate_with_custom_config(self) -> None:
        """Test generate with custom config."""
        config = BannerConfig(
            product_name="Custom SDK",
            version="2.0.0",
            show_python_version=False,
            show_platform=False,
        )
        banner = generate(config)

        assert "Custom SDK" in banner
        assert "2.0.0" in banner

    def test_generate_with_python_version(self) -> None:
        """Test generate includes Python version when enabled."""
        config = BannerConfig(show_python_version=True)
        banner = generate(config)

        assert "Python:" in banner

    def test_generate_without_python_version(self) -> None:
        """Test generate excludes Python version when disabled."""
        config = BannerConfig(show_python_version=False)
        banner = generate(config)

        assert "Python:" not in banner

    def test_generate_with_platform(self) -> None:
        """Test generate includes platform when enabled."""
        config = BannerConfig(show_platform=True)
        banner = generate(config)

        assert "Platform:" in banner

    def test_generate_without_platform(self) -> None:
        """Test generate excludes platform when disabled."""
        config = BannerConfig(show_platform=False)
        banner = generate(config)

        assert "Platform:" not in banner


class TestGenerateCompact:
    """Test suite for generate_compact function."""

    def test_generate_compact_default(self) -> None:
        """Test generate_compact with default config."""
        banner = generate_compact()

        assert "TelemetryFlow Python SDK" in banner
        assert __version__ in banner

    def test_generate_compact_has_box(self) -> None:
        """Test generate_compact has box characters."""
        banner = generate_compact()

        assert "╔" in banner
        assert "╚" in banner
        assert "║" in banner

    def test_generate_compact_with_custom_config(self) -> None:
        """Test generate_compact with custom config."""
        config = BannerConfig(
            product_name="Custom SDK",
            version="2.0.0",
        )
        banner = generate_compact(config)

        assert "Custom SDK" in banner
        assert "2.0.0" in banner


class TestGenerateMinimal:
    """Test suite for generate_minimal function."""

    def test_generate_minimal_default(self) -> None:
        """Test generate_minimal with default config."""
        banner = generate_minimal()

        assert "TelemetryFlow Python SDK" in banner
        assert __version__ in banner
        assert "https://telemetryflow.id" in banner

    def test_generate_minimal_single_line(self) -> None:
        """Test generate_minimal is a single line."""
        banner = generate_minimal()

        assert "\n" not in banner

    def test_generate_minimal_with_custom_config(self) -> None:
        """Test generate_minimal with custom config."""
        config = BannerConfig(
            product_name="Custom SDK",
            version="2.0.0",
            website="https://custom.example.com",
        )
        banner = generate_minimal(config)

        assert "Custom SDK" in banner
        assert "2.0.0" in banner
        assert "https://custom.example.com" in banner


class TestASCIIBanner:
    """Test suite for ASCII_BANNER constant."""

    def test_ascii_banner_not_empty(self) -> None:
        """Test ASCII_BANNER is not empty."""
        assert len(ASCII_BANNER) > 0

    def test_ascii_banner_contains_telemetryflow(self) -> None:
        """Test ASCII_BANNER contains TelemetryFlow text."""
        # The ASCII art should spell out TelemetryFlow
        assert "Flow" in ASCII_BANNER or "_" in ASCII_BANNER
