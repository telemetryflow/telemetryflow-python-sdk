"""Version information for TelemetryFlow Python SDK."""

import platform
import sys

__version__ = "1.1.1"
__git_commit__ = "unknown"
__git_branch__ = "unknown"
__build_time__ = "unknown"


def info() -> str:
    """Get full version information."""
    return (
        f"TelemetryFlow Python SDK v{__version__}\n"
        f"Git Commit: {__git_commit__}\n"
        f"Git Branch: {__git_branch__}\n"
        f"Build Time: {__build_time__}\n"
        f"Python: {python_version()}\n"
        f"Platform: {platform_info()}"
    )


def short() -> str:
    """Get short version string."""
    return __version__


def full() -> str:
    """Get version with commit."""
    return f"{__version__} ({__git_commit__[:7]})"


def python_version() -> str:
    """Get Python runtime version."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def platform_info() -> str:
    """Get OS and architecture information."""
    return f"{platform.system().lower()}/{platform.machine()}"
