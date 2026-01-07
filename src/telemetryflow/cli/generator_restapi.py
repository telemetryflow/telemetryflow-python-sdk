"""TelemetryFlow RESTful API Generator CLI.

TelemetryFlow Python SDK - Community Enterprise Observability Platform (CEOP)
Copyright (c) 2024-2026 DevOpsCorner Indonesia. All rights reserved.

Generate a complete DDD + CQRS pattern RESTful API project with Flask and SQLAlchemy.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from string import Template
from typing import Any

from telemetryflow.banner import print_banner
from telemetryflow.version import __version__

# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class EntityField:
    """Represents a field in an entity."""

    name: str
    field_type: str
    json_name: str = ""
    db_column: str = ""
    python_type: str = ""
    sqlalchemy_type: str = ""
    nullable: bool = False

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if not self.json_name:
            self.json_name = to_camel_case(self.name)
        if not self.db_column:
            self.db_column = to_snake_case(self.name)
        if not self.python_type:
            self.python_type = map_type_to_python(self.field_type)
        if not self.sqlalchemy_type:
            self.sqlalchemy_type = map_type_to_sqlalchemy(self.field_type)


@dataclass
class TemplateData:
    """Data structure for template rendering."""

    # Project info
    project_name: str = ""
    module_name: str = ""
    service_name: str = ""
    service_version: str = "1.0.0"
    environment: str = "development"
    env_prefix: str = ""

    # Database
    db_driver: str = "postgresql"
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = ""
    db_user: str = "postgres"

    # Server
    server_port: str = "5000"

    # Features
    enable_telemetry: bool = True
    enable_swagger: bool = True
    enable_cors: bool = True
    enable_auth: bool = True
    enable_rate_limit: bool = True

    # Entity (for entity generation)
    entity_name: str = ""
    entity_name_lower: str = ""
    entity_name_plural: str = ""
    entity_fields: list[EntityField] = field(default_factory=list)

    # Computed
    timestamp: str = ""

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if not self.module_name:
            self.module_name = to_snake_case(self.project_name)
        if not self.service_name:
            self.service_name = self.project_name
        if not self.db_name:
            self.db_name = to_snake_case(self.project_name).replace("-", "_")
        if not self.env_prefix:
            self.env_prefix = to_snake_case(self.project_name).upper().replace("-", "_")
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        if self.entity_name and not self.entity_name_lower:
            self.entity_name_lower = self.entity_name.lower()
        if self.entity_name and not self.entity_name_plural:
            self.entity_name_plural = pluralize(self.entity_name_lower)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template substitution."""
        result = {
            "project_name": self.project_name,
            "module_name": self.module_name,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "env_prefix": self.env_prefix,
            "db_driver": self.db_driver,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "server_port": self.server_port,
            "enable_telemetry": str(self.enable_telemetry).lower(),
            "enable_swagger": str(self.enable_swagger).lower(),
            "enable_cors": str(self.enable_cors).lower(),
            "enable_auth": str(self.enable_auth).lower(),
            "enable_rate_limit": str(self.enable_rate_limit).lower(),
            "entity_name": self.entity_name,
            "entity_name_lower": self.entity_name_lower,
            "entity_name_plural": self.entity_name_plural,
            "timestamp": self.timestamp,
        }
        return result


# =============================================================================
# STRING HELPERS
# =============================================================================


def to_pascal_case(s: str) -> str:
    """Convert string to PascalCase."""
    words = re.split(r"[_\-\s]+", s)
    return "".join(word.capitalize() for word in words)


def to_camel_case(s: str) -> str:
    """Convert string to camelCase."""
    pascal = to_pascal_case(s)
    if not pascal:
        return ""
    return pascal[0].lower() + pascal[1:]


def to_snake_case(s: str) -> str:
    """Convert string to snake_case."""
    # Insert underscore before uppercase letters
    result = re.sub(r"([A-Z])", r"_\1", s)
    # Convert to lowercase and remove leading underscore
    return result.lower().lstrip("_").replace("-", "_")


def pluralize(s: str) -> str:
    """Simple pluralization."""
    if s.endswith("s"):
        return s + "es"
    if s.endswith("y"):
        return s[:-1] + "ies"
    return s + "s"


def map_type_to_python(t: str) -> str:
    """Map field type to Python type."""
    t = t.rstrip("?")
    type_map = {
        "string": "str",
        "text": "str",
        "int": "int",
        "integer": "int",
        "int64": "int",
        "bigint": "int",
        "float": "float",
        "float64": "float",
        "decimal": "float",
        "bool": "bool",
        "boolean": "bool",
        "time": "datetime",
        "datetime": "datetime",
        "timestamp": "datetime",
        "uuid": "UUID",
        "json": "dict[str, Any]",
        "jsonb": "dict[str, Any]",
    }
    return type_map.get(t.lower(), "str")


def map_type_to_sqlalchemy(t: str) -> str:
    """Map field type to SQLAlchemy type."""
    t = t.rstrip("?")
    type_map = {
        "string": "String(255)",
        "text": "Text",
        "int": "Integer",
        "integer": "Integer",
        "int64": "BigInteger",
        "bigint": "BigInteger",
        "float": "Float",
        "float64": "Float",
        "decimal": "Numeric(10, 2)",
        "bool": "Boolean",
        "boolean": "Boolean",
        "time": "DateTime",
        "datetime": "DateTime",
        "timestamp": "DateTime",
        "uuid": "UUID",
        "json": "JSON",
        "jsonb": "JSONB",
    }
    return type_map.get(t.lower(), "String(255)")


def parse_fields(fields_str: str) -> list[EntityField]:
    """Parse field string into EntityField list."""
    if not fields_str:
        return []

    fields = []
    parts = fields_str.split(",")

    for part in parts:
        kv = part.strip().split(":")
        if len(kv) != 2:
            continue

        name = kv[0].strip()
        field_type = kv[1].strip()
        nullable = field_type.endswith("?")

        fields.append(
            EntityField(
                name=to_pascal_case(name),
                field_type=field_type,
                nullable=nullable,
            )
        )

    return fields


# =============================================================================
# TEMPLATE LOADING
# =============================================================================


def get_template_dir(subdir: str = "project") -> Path:
    """Get the templates directory path for a specific subdirectory.

    Args:
        subdir: The subdirectory within restapi templates (project, infrastructure, domain, application, entity).

    Returns:
        Path to the template directory.
    """
    try:
        with resources.as_file(
            resources.files(f"telemetryflow.cli.templates.restapi.{subdir}")
        ) as template_path:
            return template_path
    except (TypeError, AttributeError, ModuleNotFoundError):
        # Fallback for development or when resources aren't available
        cli_dir = Path(__file__).parent
        return cli_dir / "templates" / "restapi" / subdir


def load_template(
    template_name: str, subdir: str = "project", template_dir: Path | None = None
) -> str:
    """Load a template file from the specified subdirectory.

    Args:
        template_name: Name of the template file.
        subdir: Subdirectory within restapi templates.
        template_dir: Optional custom template directory.

    Returns:
        Template content as string.

    Raises:
        FileNotFoundError: If template file doesn't exist.
    """
    if template_dir is None:
        template_dir = get_template_dir(subdir)

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
    subdir: str = "project",
    template_dir: Path | None = None,
) -> str:
    """Load and render a template file.

    Args:
        template_name: Name of the template file.
        data: Template data for substitution.
        subdir: Subdirectory within restapi templates.
        template_dir: Optional custom template directory.

    Returns:
        Rendered template content.
    """
    template_str = load_template(template_name, subdir, template_dir)
    return render_template(template_str, data)


def render_with_fields(template_str: str, data: TemplateData) -> str:
    """Render a template that includes entity fields."""
    result = render_template(template_str, data)

    # Generate field-specific code
    if data.entity_fields:
        field_definitions = generate_field_definitions(data.entity_fields)
        field_columns = generate_sqlalchemy_columns(data.entity_fields)
        field_dto = generate_dto_fields(data.entity_fields)
        field_validation = generate_validation_code(data.entity_fields)

        result = result.replace("${field_definitions}", field_definitions)
        result = result.replace("${field_columns}", field_columns)
        result = result.replace("${field_dto}", field_dto)
        result = result.replace("${field_validation}", field_validation)

    return result


def render_entity_template_file(
    template_name: str,
    data: TemplateData,
    template_dir: Path | None = None,
) -> str:
    """Load and render an entity template file with field support.

    Args:
        template_name: Name of the template file.
        data: Template data for substitution.
        template_dir: Optional custom template directory.

    Returns:
        Rendered template content with fields.
    """
    template_str = load_template(template_name, "entity", template_dir)
    return render_with_fields(template_str, data)


def generate_field_definitions(fields: list[EntityField]) -> str:
    """Generate field definitions for dataclass."""
    lines = []
    for f in fields:
        nullable_suffix = " | None = None" if f.nullable else ""
        lines.append(f"    {to_snake_case(f.name)}: {f.python_type}{nullable_suffix}")
    return "\n".join(lines)


def generate_sqlalchemy_columns(fields: list[EntityField]) -> str:
    """Generate SQLAlchemy column definitions."""
    lines = []
    for f in fields:
        nullable = ", nullable=True" if f.nullable else ", nullable=False"
        lines.append(f"    {to_snake_case(f.name)} = Column({f.sqlalchemy_type}{nullable})")
    return "\n".join(lines)


def generate_dto_fields(fields: list[EntityField]) -> str:
    """Generate DTO field definitions."""
    lines = []
    for f in fields:
        nullable_suffix = " | None = None" if f.nullable else ""
        lines.append(f"    {to_snake_case(f.name)}: {f.python_type}{nullable_suffix}")
    return "\n".join(lines)


def generate_validation_code(fields: list[EntityField]) -> str:
    """Generate validation code for fields."""
    lines = []
    for f in fields:
        if not f.nullable:
            snake_name = to_snake_case(f.name)
            lines.append(f"        if not self.{snake_name}:")
            lines.append(f'            raise ValueError("{snake_name} is required")')
    return "\n".join(lines)


def write_file(path: Path, content: str, force: bool = False) -> bool:
    """Write content to a file."""
    if path.exists() and not force:
        print(f"Skipping {path} (already exists, use --force to overwrite)")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Generated: {path}")
    return True


# =============================================================================
# PROJECT GENERATOR
# =============================================================================


def generate_project(
    data: TemplateData,
    output_dir: Path,
    force: bool,
    template_dir: Path | None = None,
) -> None:
    """Generate complete project structure."""
    project_root = output_dir / data.project_name
    src_dir = project_root / "src" / data.module_name

    # Create directory structure
    dirs = [
        src_dir / "domain" / "entity",
        src_dir / "domain" / "repository",
        src_dir / "application" / "command",
        src_dir / "application" / "query",
        src_dir / "application" / "handler",
        src_dir / "application" / "dto",
        src_dir / "infrastructure" / "config",
        src_dir / "infrastructure" / "persistence",
        src_dir / "infrastructure" / "http" / "handlers",
        src_dir / "infrastructure" / "http" / "middleware",
        src_dir / "pkg",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "migrations",
        project_root / "docs",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Create __init__.py files
        init_file = d / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                '"""Auto-generated by telemetryflow-restapi."""\n', encoding="utf-8"
            )

    # Generate project files using templates
    project_tpl_dir = template_dir / "project" if template_dir else None
    infra_tpl_dir = template_dir / "infrastructure" if template_dir else None
    domain_tpl_dir = template_dir / "domain" if template_dir else None
    app_tpl_dir = template_dir / "application" if template_dir else None

    # Project root files
    write_file(
        project_root / "pyproject.toml",
        render_template_file("pyproject.toml.tpl", data, "project", project_tpl_dir),
        force,
    )
    write_file(
        project_root / ".env.example",
        render_template_file("env.example.tpl", data, "project", project_tpl_dir),
        force,
    )
    write_file(
        project_root / ".gitignore",
        render_template_file("gitignore.tpl", data, "project", project_tpl_dir),
        force,
    )
    write_file(
        project_root / "Dockerfile",
        render_template_file("Dockerfile.tpl", data, "project", project_tpl_dir),
        force,
    )
    write_file(
        project_root / "docker-compose.yml",
        render_template_file("docker-compose.yml.tpl", data, "project", project_tpl_dir),
        force,
    )
    write_file(
        project_root / "Makefile",
        render_template_file("Makefile.tpl", data, "project", project_tpl_dir),
        force,
    )
    write_file(
        project_root / "README.md",
        render_template_file("README.md.tpl", data, "project", project_tpl_dir),
        force,
    )
    write_file(
        project_root / "requirements.txt",
        render_template_file("requirements.txt.tpl", data, "project", project_tpl_dir),
        force,
    )

    # Generate source files
    write_file(
        src_dir / "__init__.py",
        f'"""{data.project_name} package."""\n__version__ = "{data.service_version}"\n',
        force,
    )
    write_file(
        src_dir / "main.py",
        render_template_file("main.py.tpl", data, "project", project_tpl_dir),
        force,
    )

    # Config
    write_file(
        src_dir / "infrastructure" / "config" / "__init__.py",
        render_template_file("config.py.tpl", data, "infrastructure", infra_tpl_dir),
        force,
    )

    # Database
    write_file(
        src_dir / "infrastructure" / "persistence" / "database.py",
        render_template_file("database.py.tpl", data, "infrastructure", infra_tpl_dir),
        force,
    )

    # HTTP
    write_file(
        src_dir / "infrastructure" / "http" / "server.py",
        render_template_file("server.py.tpl", data, "infrastructure", infra_tpl_dir),
        force,
    )
    write_file(
        src_dir / "infrastructure" / "http" / "routes.py",
        render_template_file("routes.py.tpl", data, "infrastructure", infra_tpl_dir),
        force,
    )
    write_file(
        src_dir / "infrastructure" / "http" / "middleware" / "__init__.py",
        render_template_file("middleware.py.tpl", data, "infrastructure", infra_tpl_dir),
        force,
    )
    write_file(
        src_dir / "infrastructure" / "http" / "handlers" / "health.py",
        render_template_file("health_handler.py.tpl", data, "infrastructure", infra_tpl_dir),
        force,
    )

    # Domain base
    write_file(
        src_dir / "domain" / "entity" / "base.py",
        render_template_file("base_entity.py.tpl", data, "domain", domain_tpl_dir),
        force,
    )
    write_file(
        src_dir / "domain" / "repository" / "base.py",
        render_template_file("base_repository.py.tpl", data, "domain", domain_tpl_dir),
        force,
    )

    # Application base (CQRS)
    write_file(
        src_dir / "application" / "command" / "base.py",
        render_template_file("base_command.py.tpl", data, "application", app_tpl_dir),
        force,
    )
    write_file(
        src_dir / "application" / "query" / "base.py",
        render_template_file("base_query.py.tpl", data, "application", app_tpl_dir),
        force,
    )
    write_file(
        src_dir / "application" / "handler" / "base.py",
        render_template_file("base_handler.py.tpl", data, "application", app_tpl_dir),
        force,
    )
    write_file(
        src_dir / "application" / "dto" / "base.py",
        render_template_file("base_dto.py.tpl", data, "application", app_tpl_dir),
        force,
    )

    # Pkg
    write_file(
        src_dir / "pkg" / "response.py",
        render_template_file("response.py.tpl", data, "infrastructure", infra_tpl_dir),
        force,
    )

    # Documentation
    docs_tpl_dir = template_dir / "docs" if template_dir else None
    write_file(
        project_root / "docs" / "API.md",
        render_template_file("API.md.tpl", data, "docs", docs_tpl_dir),
        force,
    )
    write_file(
        project_root / "docs" / "ARCHITECTURE.md",
        render_template_file("ARCHITECTURE.md.tpl", data, "docs", docs_tpl_dir),
        force,
    )
    write_file(
        project_root / "docs" / "DEVELOPMENT.md",
        render_template_file("DEVELOPMENT.md.tpl", data, "docs", docs_tpl_dir),
        force,
    )
    write_file(
        project_root / "docs" / "DEPLOYMENT.md",
        render_template_file("DEPLOYMENT.md.tpl", data, "docs", docs_tpl_dir),
        force,
    )

    print(f"\nProject '{data.project_name}' created successfully!")
    print("\nNext steps:")
    print(f"  1. cd {data.project_name}")
    print("  2. cp .env.example .env")
    print("  3. Edit .env with your configuration")
    print("  4. pip install -e '.[dev]'")
    print("  5. make run")
    print("\nTo add a new entity:")
    print(
        f"  telemetryflow-restapi entity -n User -f 'name:string,email:string' -o {data.project_name}"
    )


def generate_entity(
    data: TemplateData,
    output_dir: Path,
    force: bool,
    template_dir: Path | None = None,
) -> None:
    """Generate entity files."""
    src_dir = output_dir / "src" / data.module_name
    entity_tpl_dir = template_dir / "entity" if template_dir else None

    # Generate entity files
    write_file(
        src_dir / "domain" / "entity" / f"{data.entity_name_lower}.py",
        render_entity_template_file("entity.py.tpl", data, entity_tpl_dir),
        force,
    )
    write_file(
        src_dir / "domain" / "repository" / f"{data.entity_name_lower}_repository.py",
        render_entity_template_file("repository.py.tpl", data, entity_tpl_dir),
        force,
    )

    # CQRS files
    write_file(
        src_dir / "application" / "command" / f"{data.entity_name_lower}_commands.py",
        render_entity_template_file("commands.py.tpl", data, entity_tpl_dir),
        force,
    )
    write_file(
        src_dir / "application" / "query" / f"{data.entity_name_lower}_queries.py",
        render_entity_template_file("queries.py.tpl", data, entity_tpl_dir),
        force,
    )
    write_file(
        src_dir / "application" / "handler" / f"{data.entity_name_lower}_command_handler.py",
        render_entity_template_file("command_handler.py.tpl", data, entity_tpl_dir),
        force,
    )
    write_file(
        src_dir / "application" / "handler" / f"{data.entity_name_lower}_query_handler.py",
        render_entity_template_file("query_handler.py.tpl", data, entity_tpl_dir),
        force,
    )
    write_file(
        src_dir / "application" / "dto" / f"{data.entity_name_lower}_dto.py",
        render_entity_template_file("dto.py.tpl", data, entity_tpl_dir),
        force,
    )

    # Infrastructure files
    write_file(
        src_dir / "infrastructure" / "persistence" / f"{data.entity_name_lower}_repository.py",
        render_entity_template_file("persistence.py.tpl", data, entity_tpl_dir),
        force,
    )
    write_file(
        src_dir / "infrastructure" / "http" / "handlers" / f"{data.entity_name_lower}_handler.py",
        render_entity_template_file("http_handler.py.tpl", data, entity_tpl_dir),
        force,
    )

    # Migration files
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    write_file(
        output_dir / "migrations" / f"{timestamp}_create_{data.entity_name_plural}.up.sql",
        render_entity_template_file("migration_up.sql.tpl", data, entity_tpl_dir),
        force,
    )
    write_file(
        output_dir / "migrations" / f"{timestamp}_create_{data.entity_name_plural}.down.sql",
        render_entity_template_file("migration_down.sql.tpl", data, entity_tpl_dir),
        force,
    )

    print(f"\nEntity '{data.entity_name}' created successfully!")
    print("\nDon't forget to:")
    print(f"  1. Register routes in {src_dir}/infrastructure/http/routes.py")
    print("  2. Run migrations: make migrate")


# =============================================================================
# CLI COMMANDS
# =============================================================================


def cmd_new(args: argparse.Namespace) -> int:
    """Create new RESTful API project."""
    output_dir = Path(args.output or ".")
    template_dir = Path(args.template_dir) if args.template_dir else None

    data = TemplateData(
        project_name=args.name,
        module_name=args.module or to_snake_case(args.name),
        service_name=args.service or args.name,
        service_version=args.version,
        environment=args.environment,
        db_driver=args.db_driver,
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name or to_snake_case(args.name).replace("-", "_"),
        db_user=args.db_user,
        server_port=args.port,
        enable_telemetry=not args.no_telemetry,
        enable_swagger=not args.no_swagger,
        enable_cors=not args.no_cors,
        enable_auth=not args.no_auth,
        enable_rate_limit=not args.no_rate_limit,
    )

    generate_project(data, output_dir, args.force, template_dir)
    return 0


def cmd_entity(args: argparse.Namespace) -> int:
    """Add new entity to project."""
    output_dir = Path(args.output or ".")
    template_dir = Path(args.template_dir) if args.template_dir else None

    # Try to detect module name from pyproject.toml
    pyproject_path = output_dir / "pyproject.toml"
    module_name = ""
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if line.startswith("name = "):
                module_name = line.split("=")[1].strip().strip('"')
                break

    if not module_name:
        print("Error: Could not detect module name. Run this from project root or specify --module")
        return 1

    data = TemplateData(
        project_name=module_name,
        module_name=module_name,
        entity_name=to_pascal_case(args.name),
        entity_fields=parse_fields(args.fields or ""),
    )

    generate_entity(data, output_dir, args.force, template_dir)
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
        prog="telemetryflow-restapi",
        description="TelemetryFlow RESTful API Generator - Generate DDD + CQRS Flask projects",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"telemetryflow-restapi {__version__}",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Disable banner output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ===== new command =====
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new RESTful API project",
        description="Generate a complete DDD + CQRS RESTful API project structure",
    )
    new_parser.add_argument("-n", "--name", required=True, help="Project name")
    new_parser.add_argument(
        "-m", "--module", help="Python module name (defaults to snake_case of name)"
    )
    new_parser.add_argument("--service", help="Service name (defaults to project name)")
    new_parser.add_argument("--version", dest="version", default="1.0.0", help="Service version")
    new_parser.add_argument("--environment", default="development", help="Environment")
    new_parser.add_argument(
        "--db-driver", default="postgresql", help="Database driver (postgresql, mysql, sqlite)"
    )
    new_parser.add_argument("--db-host", default="localhost", help="Database host")
    new_parser.add_argument("--db-port", default="5432", help="Database port")
    new_parser.add_argument("--db-name", help="Database name (defaults to project name)")
    new_parser.add_argument("--db-user", default="postgres", help="Database user")
    new_parser.add_argument("--port", default="5000", help="Server port")
    new_parser.add_argument("-o", "--output", help="Output directory")
    new_parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files")
    new_parser.add_argument("--template-dir", help="Custom template directory")
    new_parser.add_argument("--no-telemetry", action="store_true", help="Disable TelemetryFlow")
    new_parser.add_argument("--no-swagger", action="store_true", help="Disable Swagger")
    new_parser.add_argument("--no-cors", action="store_true", help="Disable CORS")
    new_parser.add_argument("--no-auth", action="store_true", help="Disable JWT auth")
    new_parser.add_argument("--no-rate-limit", action="store_true", help="Disable rate limiting")

    # ===== entity command =====
    entity_parser = subparsers.add_parser(
        "entity",
        help="Add a new entity with full CRUD",
        description="Generate domain entity, repository, commands, queries, handlers, and API endpoints",
    )
    entity_parser.add_argument(
        "-n", "--name", required=True, help="Entity name (e.g., User, Product)"
    )
    entity_parser.add_argument(
        "-f", "--fields", help="Entity fields (e.g., 'name:string,email:string,age:int')"
    )
    entity_parser.add_argument("-o", "--output", help="Project root directory")
    entity_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    entity_parser.add_argument("--template-dir", help="Custom template directory")

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
        "new": cmd_new,
        "entity": cmd_entity,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
