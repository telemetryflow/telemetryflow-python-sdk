"""Unit tests for TelemetryFlow RESTful API Generator (telemetryflow-restapi)."""

import tempfile
from pathlib import Path

import pytest

from telemetryflow.cli.generator_restapi import (
    EntityField,
    TemplateData,
    get_template_dir,
    load_template,
    render_template,
    render_template_file,
    render_entity_template_file,
    to_pascal_case,
    to_camel_case,
    to_snake_case,
    pluralize,
    map_type_to_python,
    map_type_to_sqlalchemy,
    parse_fields,
    generate_field_definitions,
    generate_sqlalchemy_columns,
    generate_dto_fields,
    main,
)


class TestStringHelpers:
    """Test suite for string helper functions."""

    def test_to_pascal_case(self) -> None:
        """Test converting to PascalCase."""
        assert to_pascal_case("hello_world") == "HelloWorld"
        assert to_pascal_case("hello-world") == "HelloWorld"
        assert to_pascal_case("hello world") == "HelloWorld"
        assert to_pascal_case("user") == "User"
        assert to_pascal_case("user_profile") == "UserProfile"

    def test_to_camel_case(self) -> None:
        """Test converting to camelCase."""
        assert to_camel_case("hello_world") == "helloWorld"
        assert to_camel_case("hello-world") == "helloWorld"
        assert to_camel_case("user") == "user"
        assert to_camel_case("user_profile") == "userProfile"

    def test_to_snake_case(self) -> None:
        """Test converting to snake_case."""
        assert to_snake_case("HelloWorld") == "hello_world"
        assert to_snake_case("helloWorld") == "hello_world"
        assert to_snake_case("User") == "user"
        assert to_snake_case("UserProfile") == "user_profile"

    def test_pluralize(self) -> None:
        """Test pluralization."""
        assert pluralize("user") == "users"
        assert pluralize("class") == "classes"
        assert pluralize("category") == "categories"
        assert pluralize("product") == "products"


class TestTypeMapping:
    """Test suite for type mapping functions."""

    def test_map_type_to_python(self) -> None:
        """Test mapping types to Python types."""
        assert map_type_to_python("string") == "str"
        assert map_type_to_python("text") == "str"
        assert map_type_to_python("int") == "int"
        assert map_type_to_python("integer") == "int"
        assert map_type_to_python("int64") == "int"
        assert map_type_to_python("float") == "float"
        assert map_type_to_python("bool") == "bool"
        assert map_type_to_python("datetime") == "datetime"
        assert map_type_to_python("uuid") == "UUID"
        assert map_type_to_python("json") == "dict[str, Any]"

    def test_map_type_to_python_nullable(self) -> None:
        """Test mapping nullable types to Python types."""
        assert map_type_to_python("string?") == "str"
        assert map_type_to_python("int?") == "int"

    def test_map_type_to_sqlalchemy(self) -> None:
        """Test mapping types to SQLAlchemy types."""
        assert map_type_to_sqlalchemy("string") == "String(255)"
        assert map_type_to_sqlalchemy("text") == "Text"
        assert map_type_to_sqlalchemy("int") == "Integer"
        assert map_type_to_sqlalchemy("int64") == "BigInteger"
        assert map_type_to_sqlalchemy("float") == "Float"
        assert map_type_to_sqlalchemy("bool") == "Boolean"
        assert map_type_to_sqlalchemy("datetime") == "DateTime"
        assert map_type_to_sqlalchemy("uuid") == "UUID"
        assert map_type_to_sqlalchemy("json") == "JSON"


class TestEntityField:
    """Test suite for EntityField dataclass."""

    def test_create_entity_field(self) -> None:
        """Test creating entity field with defaults."""
        field = EntityField(name="Name", field_type="string")

        assert field.name == "Name"
        assert field.field_type == "string"
        assert field.json_name == "name"
        assert field.db_column == "name"
        assert field.python_type == "str"
        assert field.sqlalchemy_type == "String(255)"
        assert field.nullable is False

    def test_create_entity_field_nullable(self) -> None:
        """Test creating nullable entity field."""
        field = EntityField(name="Description", field_type="text?", nullable=True)

        assert field.nullable is True
        assert field.python_type == "str"


class TestParseFields:
    """Test suite for field parsing."""

    def test_parse_fields_simple(self) -> None:
        """Test parsing simple field string."""
        fields = parse_fields("name:string,email:string")

        assert len(fields) == 2
        assert fields[0].name == "Name"
        assert fields[0].python_type == "str"
        assert fields[1].name == "Email"

    def test_parse_fields_with_types(self) -> None:
        """Test parsing fields with various types."""
        fields = parse_fields("id:uuid,count:int,price:float,active:bool")

        assert len(fields) == 4
        assert fields[0].python_type == "UUID"
        assert fields[1].python_type == "int"
        assert fields[2].python_type == "float"
        assert fields[3].python_type == "bool"

    def test_parse_fields_empty(self) -> None:
        """Test parsing empty field string."""
        fields = parse_fields("")
        assert len(fields) == 0

    def test_parse_fields_nullable(self) -> None:
        """Test parsing nullable field."""
        fields = parse_fields("description:text?")

        assert len(fields) == 1
        assert fields[0].nullable is True


class TestTemplateData:
    """Test suite for TemplateData."""

    def test_create_template_data(self) -> None:
        """Test creating template data with defaults."""
        data = TemplateData(project_name="MyProject")

        assert data.project_name == "MyProject"
        assert data.module_name == "my_project"
        assert data.service_name == "MyProject"
        assert data.db_name == "my_project"
        assert data.env_prefix == "MY_PROJECT"

    def test_template_data_entity(self) -> None:
        """Test creating template data with entity."""
        data = TemplateData(
            project_name="MyProject",
            entity_name="User",
        )

        assert data.entity_name == "User"
        assert data.entity_name_lower == "user"
        assert data.entity_name_plural == "users"

    def test_template_data_to_dict(self) -> None:
        """Test converting template data to dictionary."""
        data = TemplateData(project_name="TestProject")
        result = data.to_dict()

        assert isinstance(result, dict)
        assert result["project_name"] == "TestProject"
        assert result["module_name"] == "test_project"


class TestTemplateLoading:
    """Test suite for template loading functions."""

    def test_get_template_dir_project(self) -> None:
        """Test getting project template directory."""
        template_dir = get_template_dir("project")

        assert template_dir.exists()
        assert (template_dir / "pyproject.toml.tpl").exists()

    def test_get_template_dir_infrastructure(self) -> None:
        """Test getting infrastructure template directory."""
        template_dir = get_template_dir("infrastructure")

        assert template_dir.exists()
        assert (template_dir / "config.py.tpl").exists()

    def test_get_template_dir_domain(self) -> None:
        """Test getting domain template directory."""
        template_dir = get_template_dir("domain")

        assert template_dir.exists()
        assert (template_dir / "base_entity.py.tpl").exists()

    def test_get_template_dir_application(self) -> None:
        """Test getting application template directory."""
        template_dir = get_template_dir("application")

        assert template_dir.exists()
        assert (template_dir / "base_command.py.tpl").exists()

    def test_get_template_dir_entity(self) -> None:
        """Test getting entity template directory."""
        template_dir = get_template_dir("entity")

        assert template_dir.exists()
        assert (template_dir / "entity.py.tpl").exists()

    def test_load_template_pyproject(self) -> None:
        """Test loading pyproject.toml template."""
        content = load_template("pyproject.toml.tpl", "project")

        assert "[project]" in content
        assert "${module_name}" in content

    def test_load_template_main(self) -> None:
        """Test loading main.py template."""
        content = load_template("main.py.tpl", "project")

        assert "def main(" in content
        assert "${module_name}" in content

    def test_load_template_config(self) -> None:
        """Test loading config template."""
        content = load_template("config.py.tpl", "infrastructure")

        assert "class Config:" in content
        assert "from_env" in content

    def test_load_template_base_entity(self) -> None:
        """Test loading base entity template."""
        content = load_template("base_entity.py.tpl", "domain")

        assert "class BaseEntity" in content
        assert "SQLAlchemy" in content or "Column" in content

    def test_load_template_not_found(self) -> None:
        """Test loading non-existent template raises error."""
        with pytest.raises(FileNotFoundError):
            load_template("nonexistent.tpl", "project")


class TestTemplateRendering:
    """Test suite for template rendering functions."""

    def test_render_template_simple(self) -> None:
        """Test rendering a simple template."""
        template = "Project: ${project_name}, Module: ${module_name}"
        data = TemplateData(project_name="TestProject")

        result = render_template(template, data)

        assert result == "Project: TestProject, Module: test_project"

    def test_render_template_file(self) -> None:
        """Test rendering a template file."""
        data = TemplateData(
            project_name="TestProject",
            service_version="1.0.0",
        )

        result = render_template_file("pyproject.toml.tpl", data, "project")

        assert "test_project" in result
        assert "1.0.0" in result


class TestFieldGeneration:
    """Test suite for field code generation."""

    def test_generate_field_definitions(self) -> None:
        """Test generating field definitions."""
        fields = [
            EntityField(name="Name", field_type="string"),
            EntityField(name="Age", field_type="int"),
        ]

        result = generate_field_definitions(fields)

        assert "name: str" in result
        assert "age: int" in result

    def test_generate_field_definitions_nullable(self) -> None:
        """Test generating nullable field definitions."""
        fields = [
            EntityField(name="Description", field_type="text?", nullable=True),
        ]

        result = generate_field_definitions(fields)

        assert "description: str | None = None" in result

    def test_generate_sqlalchemy_columns(self) -> None:
        """Test generating SQLAlchemy columns."""
        fields = [
            EntityField(name="Name", field_type="string"),
            EntityField(name="Active", field_type="bool"),
        ]

        result = generate_sqlalchemy_columns(fields)

        assert "name = Column(String(255)" in result
        assert "active = Column(Boolean" in result
        assert "nullable=False" in result

    def test_generate_dto_fields(self) -> None:
        """Test generating DTO fields."""
        fields = [
            EntityField(name="Title", field_type="string"),
            EntityField(name="Count", field_type="int"),
        ]

        result = generate_dto_fields(fields)

        assert "title: str" in result
        assert "count: int" in result


class TestEntityTemplateRendering:
    """Test suite for entity template rendering."""

    def test_render_entity_template(self) -> None:
        """Test rendering entity template."""
        data = TemplateData(
            project_name="TestProject",
            entity_name="User",
            entity_fields=[
                EntityField(name="Name", field_type="string"),
                EntityField(name="Email", field_type="string"),
            ],
        )

        result = render_entity_template_file("entity.py.tpl", data)

        assert "class User" in result
        assert "__tablename__" in result


class TestCLI:
    """Test suite for CLI main function."""

    def test_cli_version(self) -> None:
        """Test CLI version command."""
        result = main(["version"])
        assert result == 0

    def test_cli_help(self) -> None:
        """Test CLI help (no command)."""
        result = main([])
        assert result == 0

    def test_cli_new_creates_project(self) -> None:
        """Test CLI new command creates project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main([
                "--no-banner",
                "new",
                "-n", "test-project",
                "-o", tmpdir,
            ])

            assert result == 0

            # Check project directory was created
            project_dir = Path(tmpdir) / "test-project"
            assert project_dir.exists()

            # Check key files were created
            assert (project_dir / "pyproject.toml").exists()
            assert (project_dir / "Dockerfile").exists()
            assert (project_dir / "docker-compose.yml").exists()
            assert (project_dir / "Makefile").exists()
            assert (project_dir / "README.md").exists()
            assert (project_dir / ".env.example").exists()

            # Check source structure
            src_dir = project_dir / "src" / "test_project"
            assert src_dir.exists()
            assert (src_dir / "main.py").exists()
            assert (src_dir / "infrastructure" / "config" / "__init__.py").exists()
            assert (src_dir / "infrastructure" / "http" / "server.py").exists()
            assert (src_dir / "domain" / "entity" / "base.py").exists()
            assert (src_dir / "application" / "command" / "base.py").exists()

    def test_cli_new_with_custom_options(self) -> None:
        """Test CLI new command with custom options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main([
                "--no-banner",
                "new",
                "-n", "custom-api",
                "-o", tmpdir,
                "--port", "8080",
                "--db-driver", "sqlite",
                "--environment", "testing",
                "--force",  # Force to overwrite __init__.py with config
            ])

            assert result == 0

            # Check config contains custom values
            project_dir = Path(tmpdir) / "custom-api"
            config_file = project_dir / "src" / "custom_api" / "infrastructure" / "config" / "__init__.py"
            config_content = config_file.read_text()

            assert "8080" in config_content
            assert "sqlite" in config_content
            assert "testing" in config_content


class TestProjectTemplates:
    """Test suite for project templates."""

    def test_dockerfile_template(self) -> None:
        """Test Dockerfile template."""
        content = load_template("Dockerfile.tpl", "project")

        assert "FROM python" in content
        assert "WORKDIR" in content
        assert "EXPOSE" in content
        assert "${server_port}" in content

    def test_docker_compose_template(self) -> None:
        """Test docker-compose.yml template."""
        content = load_template("docker-compose.yml.tpl", "project")

        assert "services:" in content
        assert "postgres" in content
        assert "${module_name}" in content

    def test_makefile_template(self) -> None:
        """Test Makefile template."""
        content = load_template("Makefile.tpl", "project")

        assert "install:" in content
        assert "test:" in content
        assert "run:" in content

    def test_readme_template(self) -> None:
        """Test README.md template."""
        content = load_template("README.md.tpl", "project")

        assert "${project_name}" in content
        assert "DDD" in content or "Flask" in content


class TestInfrastructureTemplates:
    """Test suite for infrastructure templates."""

    def test_server_template(self) -> None:
        """Test server.py template."""
        content = load_template("server.py.tpl", "infrastructure")

        assert "Flask" in content
        assert "create_app" in content

    def test_routes_template(self) -> None:
        """Test routes.py template."""
        content = load_template("routes.py.tpl", "infrastructure")

        assert "register_routes" in content
        assert "health_bp" in content

    def test_middleware_template(self) -> None:
        """Test middleware.py template."""
        content = load_template("middleware.py.tpl", "infrastructure")

        assert "setup_middleware" in content
        assert "CORS" in content or "JWT" in content

    def test_database_template(self) -> None:
        """Test database.py template."""
        content = load_template("database.py.tpl", "infrastructure")

        assert "SQLAlchemy" in content
        assert "init_db" in content

    def test_health_handler_template(self) -> None:
        """Test health_handler.py template."""
        content = load_template("health_handler.py.tpl", "infrastructure")

        assert "health" in content.lower()
        assert "Blueprint" in content


class TestApplicationTemplates:
    """Test suite for application templates (CQRS)."""

    def test_base_command_template(self) -> None:
        """Test base_command.py template."""
        content = load_template("base_command.py.tpl", "application")

        assert "class Command" in content
        assert "dataclass" in content

    def test_base_query_template(self) -> None:
        """Test base_query.py template."""
        content = load_template("base_query.py.tpl", "application")

        assert "class Query" in content
        assert "PaginatedQuery" in content

    def test_base_handler_template(self) -> None:
        """Test base_handler.py template."""
        content = load_template("base_handler.py.tpl", "application")

        assert "CommandHandler" in content
        assert "QueryHandler" in content
        assert "handle" in content

    def test_base_dto_template(self) -> None:
        """Test base_dto.py template."""
        content = load_template("base_dto.py.tpl", "application")

        assert "BaseDTO" in content
        assert "PaginatedResponse" in content


class TestEntityTemplates:
    """Test suite for entity templates."""

    def test_entity_template(self) -> None:
        """Test entity.py template."""
        content = load_template("entity.py.tpl", "entity")

        assert "${entity_name}" in content
        assert "__tablename__" in content

    def test_repository_template(self) -> None:
        """Test repository.py template."""
        content = load_template("repository.py.tpl", "entity")

        assert "${entity_name}Repository" in content
        assert "find_by_id" in content

    def test_commands_template(self) -> None:
        """Test commands.py template."""
        content = load_template("commands.py.tpl", "entity")

        assert "Create${entity_name}Command" in content
        assert "Update${entity_name}Command" in content
        assert "Delete${entity_name}Command" in content

    def test_queries_template(self) -> None:
        """Test queries.py template."""
        content = load_template("queries.py.tpl", "entity")

        assert "Get${entity_name}ByIdQuery" in content
        assert "List${entity_name_plural}Query" in content

    def test_http_handler_template(self) -> None:
        """Test http_handler.py template."""
        content = load_template("http_handler.py.tpl", "entity")

        assert "Blueprint" in content
        assert "GET" in content
        assert "POST" in content
        assert "PUT" in content
        assert "DELETE" in content

    def test_persistence_template(self) -> None:
        """Test persistence.py template."""
        content = load_template("persistence.py.tpl", "entity")

        assert "SQLAlchemy${entity_name}Repository" in content
        assert "db.session" in content

    def test_migration_templates(self) -> None:
        """Test migration templates."""
        up_content = load_template("migration_up.sql.tpl", "entity")
        down_content = load_template("migration_down.sql.tpl", "entity")

        assert "CREATE TABLE" in up_content
        assert "DROP TABLE" in down_content
