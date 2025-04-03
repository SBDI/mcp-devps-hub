@echo off

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run linting
echo Running Ruff...
ruff check .

REM Run type checking
echo Running MyPy...
mypy src\mcp_devops_hub

REM Run tests
echo Running tests...
pytest tests\