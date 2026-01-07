[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "${module_name}"
version = "${service_version}"
description = "${project_name} - RESTful API with DDD + CQRS pattern"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.12"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

dependencies = [
    "flask>=3.0.0",
    "flask-cors>=4.0.0",
    "flask-limiter>=3.5.0",
    "flask-jwt-extended>=4.6.0",
    "flask-sqlalchemy>=3.1.0",
    "flasgger>=0.9.7",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.9",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
    "telemetryflow-python-sdk>=1.1.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-flask>=1.3.0",
    "httpx>=0.26.0",
    "mypy>=1.8.0",
    "ruff>=0.1.0",
    "black>=24.0.0",
]

[project.scripts]
${module_name} = "${module_name}.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.mypy]
python_version = "3.12"
strict = true

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.black]
target-version = ["py312"]
line-length = 100
