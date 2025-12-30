"""Banner utilities for TelemetryFlow SDK."""

from __future__ import annotations

from dataclasses import dataclass

from telemetryflow.version import __version__, platform_info, python_version

# ASCII art banner
ASCII_BANNER = r"""
    ___________    .__                        __
    \__    ___/___ |  |   ____   _____   _____/  |________ ___.__.
      |    |_/ __ \|  | _/ __ \ /     \_/ __ \   __\_  __ <   |  |
      |    |\  ___/|  |_\  ___/|  Y Y  \  ___/|  |  |  | \/\___  |
      |____| \___  >____/\___  >__|_|  /\___  >__|  |__|   / ____|
                 \/          \/      \/     \/             \/
                    ___________.__
                    \_   _____/|  |   ______  _  __
                     |    __)  |  |  /  _ \ \/ \/ /
                     |     \   |  |_(  <_> )     /
                     |___  /   |____/\____/ \/\_/
                         \/
              _________  ________   ____  __.
             /   _____/ \______ \ |    |/ _|
             \_____  \   |    |  \|      <
             /        \  |    '   \    |  \
            /_______  / /_______  /____|__ \
                    \/          \/        \/

"""

COMPACT_BANNER = r"""
╔═══════════════════════════════════════════════════════════════╗
║           TelemetryFlow Python SDK                            ║
╚═══════════════════════════════════════════════════════════════╝
"""


@dataclass
class BannerConfig:
    """Configuration for banner display."""

    product_name: str = "TelemetryFlow Python SDK"
    version: str = __version__
    vendor: str = "TelemetryFlow"
    website: str = "https://telemetryflow.id"
    show_python_version: bool = True
    show_platform: bool = True


def generate(config: BannerConfig | None = None) -> str:
    """
    Generate a full banner with ASCII art.

    Args:
        config: Optional banner configuration

    Returns:
        Formatted banner string
    """
    if config is None:
        config = BannerConfig()

    lines = [
        ASCII_BANNER.strip(),
        "",
        f"  {config.product_name} v{config.version}",
        f"  {config.website}",
    ]

    if config.show_python_version:
        lines.append(f"  Python: {python_version()}")

    if config.show_platform:
        lines.append(f"  Platform: {platform_info()}")

    lines.append("")

    return "\n".join(lines)


def generate_compact(config: BannerConfig | None = None) -> str:
    """
    Generate a compact banner.

    Args:
        config: Optional banner configuration

    Returns:
        Formatted compact banner string
    """
    if config is None:
        config = BannerConfig()

    return f"""
╔═══════════════════════════════════════════════════════════════╗
║  {config.product_name:^57}  ║
║  Version: {config.version:<48}  ║
║  {config.website:<57}  ║
╚═══════════════════════════════════════════════════════════════╝
""".strip()


def generate_minimal(config: BannerConfig | None = None) -> str:
    """
    Generate a minimal single-line banner.

    Args:
        config: Optional banner configuration

    Returns:
        Minimal banner string
    """
    if config is None:
        config = BannerConfig()

    return f"{config.product_name} v{config.version} | {config.website}"


def print_banner(config: BannerConfig | None = None) -> None:
    """
    Print the full banner to stdout.

    Args:
        config: Optional banner configuration
    """
    print(generate(config))


def print_compact(config: BannerConfig | None = None) -> None:
    """
    Print the compact banner to stdout.

    Args:
        config: Optional banner configuration
    """
    print(generate_compact(config))


def print_minimal(config: BannerConfig | None = None) -> None:
    """
    Print the minimal banner to stdout.

    Args:
        config: Optional banner configuration
    """
    print(generate_minimal(config))
