"""TelemetryFlow SDK Generator CLI.

TelemetryFlow Python SDK - Community Enterprise Observability Platform (CEOP)
Copyright (c) 2024-2026 DevOpsCorner Indonesia. All rights reserved.

Generate boilerplate code for integrating TelemetryFlow into your Python application.
"""

from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path
from string import Template
from typing import Any

from telemetryflow.banner import print_banner
from telemetryflow.version import __version__

# =============================================================================
# TEMPLATE DATA STRUCTURES
# =============================================================================


class TemplateData:
    """Data structure for template rendering."""

    def __init__(
        self,
        project_name: str = "",
        service_name: str = "",
        service_version: str = "1.0.0",
        environment: str = "production",
        api_key_id: str = "",
        api_key_secret: str = "",
        endpoint: str = "localhost:4317",
        enable_metrics: bool = True,
        enable_logs: bool = True,
        enable_traces: bool = True,
        port: str = "8080",
        # TFO v2 API settings (aligned with TFO-Collector v1.1.2)
        use_v2_api: bool = True,
        v2_only: bool = False,
        collector_name: str = "TelemetryFlow Python SDK",
        datacenter: str = "default",
        enrich_resources: bool = True,
        protocol: str = "grpc",
    ) -> None:
        self.project_name = project_name
        self.service_name = service_name or project_name
        self.service_version = service_version
        self.environment = environment
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.endpoint = endpoint
        self.enable_metrics = enable_metrics
        self.enable_logs = enable_logs
        self.enable_traces = enable_traces
        self.port = port
        # TFO v2 API fields
        self.use_v2_api = use_v2_api
        self.v2_only = v2_only
        self.collector_name = collector_name
        self.datacenter = datacenter
        self.enrich_resources = enrich_resources
        self.protocol = protocol

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template substitution."""
        return {
            "project_name": self.project_name,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "api_key_id": self.api_key_id or "tfk_your_key_id",
            "api_key_secret": self.api_key_secret or "tfs_your_key_secret",
            "endpoint": self.endpoint,
            "enable_metrics": str(self.enable_metrics).lower(),
            "enable_logs": str(self.enable_logs).lower(),
            "enable_traces": str(self.enable_traces).lower(),
            "port": self.port,
            # TFO v2 API fields
            "use_v2_api": str(self.use_v2_api).lower(),
            "v2_only": str(self.v2_only).lower(),
            "collector_name": self.collector_name,
            "datacenter": self.datacenter,
            "enrich_resources": str(self.enrich_resources).lower(),
            "protocol": self.protocol,
            "sdk_version": __version__,
            "tfo_collector_version": "1.1.2",
        }


# =============================================================================
# TEMPLATE LOADING
# =============================================================================


def get_template_dir() -> Path:
    """Get the templates directory path."""
    # Use importlib.resources for Python 3.9+
    try:
        with resources.as_file(
            resources.files("telemetryflow.cli.templates.native")
        ) as template_path:
            return template_path
    except (TypeError, AttributeError):
        # Fallback for older Python or if resources aren't properly installed
        cli_dir = Path(__file__).parent
        return cli_dir / "templates" / "native"


def load_template(template_name: str, template_dir: Path | None = None) -> str:
    """Load a template file.

    Args:
        template_name: Name of the template file (e.g., "env.tpl").
        template_dir: Optional custom template directory.

    Returns:
        Template content as string.
    """
    if template_dir is None:
        template_dir = get_template_dir()

    template_path = template_dir / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")


def render_template(template_str: str, data: TemplateData) -> str:
    """Render a template with the given data."""
    template = Template(template_str)
    return template.safe_substitute(data.to_dict())


def render_template_file(
    template_name: str,
    data: TemplateData,
    template_dir: Path | None = None,
) -> str:
    """Load and render a template file.

    Args:
        template_name: Name of the template file.
        data: Template data for substitution.
        template_dir: Optional custom template directory.

    Returns:
        Rendered template content.
    """
    template_str = load_template(template_name, template_dir)
    return render_template(template_str, data)


# =============================================================================
# FILE GENERATORS
# =============================================================================


def write_file(path: Path, content: str, force: bool = False) -> bool:
    """Write content to a file.

    Args:
        path: File path.
        content: File content.
        force: Overwrite existing files.

    Returns:
        True if file was written, False otherwise.
    """
    if path.exists() and not force:
        print(f"Skipping {path} (already exists, use --force to overwrite)")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Generated: {path}")
    return True


def generate_init_files(
    output_dir: Path,
    data: TemplateData,
    force: bool,
    template_dir: Path | None = None,
) -> None:
    """Generate telemetry integration files."""
    telemetry_dir = output_dir / "telemetry"

    # Main init module
    write_file(
        telemetry_dir / "__init__.py",
        render_template_file("init.py.tpl", data, template_dir),
        force,
    )

    # Metrics module
    write_file(
        telemetry_dir / "metrics.py",
        render_template_file("metrics.py.tpl", data, template_dir),
        force,
    )

    # Logs module
    write_file(
        telemetry_dir / "logs.py",
        render_template_file("logs.py.tpl", data, template_dir),
        force,
    )

    # Traces module
    write_file(
        telemetry_dir / "traces.py",
        render_template_file("traces.py.tpl", data, template_dir),
        force,
    )

    # README
    write_file(
        telemetry_dir / "README.md",
        render_template_file("README.md.tpl", data, template_dir),
        force,
    )


def generate_config_file(
    output_dir: Path,
    data: TemplateData,
    force: bool,
    template_dir: Path | None = None,
) -> None:
    """Generate environment configuration file."""
    write_file(
        output_dir / ".env.telemetryflow",
        render_template_file("env.tpl", data, template_dir),
        force,
    )


def generate_example(
    example_type: str,
    output_dir: Path,
    data: TemplateData,
    force: bool,
    template_dir: Path | None = None,
) -> bool:
    """Generate example code.

    Args:
        example_type: Type of example (basic, http-server, grpc-server, worker).
        output_dir: Output directory.
        data: Template data.
        force: Overwrite existing files.
        template_dir: Optional custom template directory.

    Returns:
        True if successful, False otherwise.
    """
    examples = {
        "basic": ("example_basic.py", "example_basic.py.tpl"),
        "http-server": ("example_http_server.py", "example_http_server.py.tpl"),
        "grpc-server": ("example_grpc_server.py", "example_grpc_server.py.tpl"),
        "worker": ("example_worker.py", "example_worker.py.tpl"),
    }

    if example_type not in examples:
        print(f"Error: Unknown example type '{example_type}'")
        print(f"Available types: {', '.join(examples.keys())}")
        return False

    filename, template_name = examples[example_type]
    try:
        content = render_template_file(template_name, data, template_dir)
        return write_file(output_dir / filename, content, force)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return False


# =============================================================================
# CLI COMMANDS
# =============================================================================


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize TelemetryFlow in the current project."""
    output_dir = Path(args.output or ".")
    template_dir = Path(args.template_dir) if args.template_dir else None

    data = TemplateData(
        project_name=args.project or output_dir.name,
        service_name=args.service or args.project or output_dir.name,
        service_version=args.version or "1.0.0",
        environment=args.environment or "production",
        api_key_id=args.key_id or "",
        api_key_secret=args.key_secret or "",
        endpoint=args.endpoint or "localhost:4317",
        enable_metrics=not args.no_metrics,
        enable_logs=not args.no_logs,
        enable_traces=not args.no_traces,
        # TFO v2 API settings
        use_v2_api=getattr(args, "use_v2_api", True),
        v2_only=getattr(args, "v2_only", False),
        collector_name=getattr(args, "collector_name", None) or "TelemetryFlow Python SDK",
        datacenter=getattr(args, "datacenter", None) or "default",
        protocol=getattr(args, "protocol", None) or "grpc",
    )

    print(f"Initializing TelemetryFlow integration for project: {data.project_name}")

    # Generate files
    generate_config_file(output_dir, data, args.force, template_dir)
    generate_init_files(output_dir, data, args.force, template_dir)

    # Generate basic example
    generate_example("basic", output_dir, data, args.force, template_dir)

    print("\nTelemetryFlow initialized successfully!")
    print("\nNext steps:")
    print("1. Edit .env.telemetryflow with your API credentials")
    print("2. Import the telemetry module in your code:")
    print("   from telemetry import init, get_client")
    print("3. Initialize at startup:")
    print("   init()")
    print("\nFor more information, visit https://docs.telemetryflow.id")

    return 0


def cmd_example(args: argparse.Namespace) -> int:
    """Generate example code."""
    output_dir = Path(args.output or ".")
    template_dir = Path(args.template_dir) if args.template_dir else None

    data = TemplateData(
        project_name=output_dir.name,
        service_version="1.0.0",
        port=args.port or "8080",
    )

    if generate_example(args.type, output_dir, data, args.force, template_dir):
        return 0
    return 1


def cmd_config(args: argparse.Namespace) -> int:
    """Generate configuration file."""
    output_dir = Path(args.output or ".")
    template_dir = Path(args.template_dir) if args.template_dir else None

    data = TemplateData(
        project_name=output_dir.name,
        service_name=args.service or output_dir.name,
        service_version=args.version or "1.0.0",
        environment=args.environment or "production",
        api_key_id=args.key_id or "",
        api_key_secret=args.key_secret or "",
        endpoint=args.endpoint or "localhost:4317",
        # TFO v2 API settings
        use_v2_api=getattr(args, "use_v2_api", True),
        v2_only=getattr(args, "v2_only", False),
        collector_name=getattr(args, "collector_name", None) or "TelemetryFlow Python SDK",
        datacenter=getattr(args, "datacenter", None) or "default",
        protocol=getattr(args, "protocol", None) or "grpc",
    )

    generate_config_file(output_dir, data, args.force, template_dir)
    print("Configuration file generated: .env.telemetryflow")
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    """Show version information."""
    from telemetryflow.version import info

    print(info())
    return 0


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="telemetryflow-gen",
        description="TelemetryFlow SDK Generator - Generate boilerplate code for TelemetryFlow integration",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"telemetryflow-gen {__version__}",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Disable banner output",
    )
    parser.add_argument(
        "--template-dir",
        help="Custom template directory (uses embedded templates if not set)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ===== init command =====
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize TelemetryFlow in your project",
        description="Generate all necessary files to integrate TelemetryFlow into your project",
    )
    init_parser.add_argument("-p", "--project", help="Project name")
    init_parser.add_argument("-n", "--service", help="Service name (defaults to project name)")
    init_parser.add_argument("--version", dest="version", help="Service version", default="1.0.0")
    init_parser.add_argument("-k", "--key-id", help="TelemetryFlow API Key ID")
    init_parser.add_argument("-s", "--key-secret", help="TelemetryFlow API Key Secret")
    init_parser.add_argument(
        "-e",
        "--endpoint",
        help="OTLP endpoint",
        default="localhost:4317",
    )
    init_parser.add_argument(
        "--environment",
        help="Environment (development, staging, production)",
        default="production",
    )
    init_parser.add_argument("-o", "--output", help="Output directory")
    init_parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files")
    init_parser.add_argument("--no-metrics", action="store_true", help="Disable metrics")
    init_parser.add_argument("--no-logs", action="store_true", help="Disable logs")
    init_parser.add_argument("--no-traces", action="store_true", help="Disable traces")
    init_parser.add_argument("--template-dir", help="Custom template directory")
    # TFO v2 API options
    init_parser.add_argument(
        "--use-v2-api",
        dest="use_v2_api",
        action="store_true",
        default=True,
        help="Enable TFO v2 API endpoints (default: true)",
    )
    init_parser.add_argument(
        "--v2-only",
        dest="v2_only",
        action="store_true",
        default=False,
        help="Enable v2-only mode (disables v1 endpoints)",
    )
    init_parser.add_argument(
        "--collector-name",
        help="Collector name for identity",
        default="TelemetryFlow Python SDK",
    )
    init_parser.add_argument(
        "--datacenter",
        help="Datacenter/region identifier",
        default="default",
    )
    init_parser.add_argument(
        "--protocol",
        choices=["grpc", "http"],
        help="Protocol (grpc or http)",
        default="grpc",
    )

    # ===== example command =====
    example_parser = subparsers.add_parser(
        "example",
        help="Generate example code",
        description="Generate example code for specific use cases",
    )
    example_parser.add_argument(
        "type",
        choices=["basic", "http-server", "grpc-server", "worker"],
        help="Example type",
    )
    example_parser.add_argument("-o", "--output", help="Output directory")
    example_parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite existing files"
    )
    example_parser.add_argument(
        "--port", help="Server port (for http-server example)", default="8080"
    )
    example_parser.add_argument("--template-dir", help="Custom template directory")

    # ===== config command =====
    config_parser = subparsers.add_parser(
        "config",
        help="Generate configuration file",
        description="Generate a .env configuration file with TelemetryFlow settings",
    )
    config_parser.add_argument("-n", "--service", help="Service name")
    config_parser.add_argument("--version", dest="version", help="Service version", default="1.0.0")
    config_parser.add_argument("-k", "--key-id", help="TelemetryFlow API Key ID")
    config_parser.add_argument("-s", "--key-secret", help="TelemetryFlow API Key Secret")
    config_parser.add_argument("-e", "--endpoint", help="OTLP endpoint", default="localhost:4317")
    config_parser.add_argument("--environment", help="Environment", default="production")
    config_parser.add_argument("-o", "--output", help="Output directory")
    config_parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite existing files"
    )
    config_parser.add_argument("--template-dir", help="Custom template directory")
    # TFO v2 API options
    config_parser.add_argument(
        "--use-v2-api",
        dest="use_v2_api",
        action="store_true",
        default=True,
        help="Enable TFO v2 API endpoints",
    )
    config_parser.add_argument(
        "--v2-only",
        dest="v2_only",
        action="store_true",
        default=False,
        help="Enable v2-only mode",
    )
    config_parser.add_argument(
        "--collector-name",
        help="Collector name for identity",
        default="TelemetryFlow Python SDK",
    )
    config_parser.add_argument("--datacenter", help="Datacenter/region", default="default")
    config_parser.add_argument("--protocol", choices=["grpc", "http"], default="grpc")

    # ===== version command =====
    subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args(argv)

    # Show banner unless disabled
    if not args.no_banner and args.command != "version":
        print_banner()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "init": cmd_init,
        "example": cmd_example,
        "config": cmd_config,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
