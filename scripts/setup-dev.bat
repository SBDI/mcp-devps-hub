@echo off

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Clean existing installations
echo Cleaning existing packages...
uv pip uninstall fastmcp mcp

REM Install core dependencies first
echo Installing core dependencies...
uv pip install "mcp>=1.6.0" "fastmcp==0.4.1"

REM Install remaining dependencies
echo Installing remaining dependencies...
uv pip install -r requirements.txt

REM Install dev dependencies
echo Installing dev dependencies...
uv pip install -r requirements-dev.txt

REM Install the package in editable mode
echo Installing package in editable mode...
uv pip install -e .

echo Development environment setup complete!
