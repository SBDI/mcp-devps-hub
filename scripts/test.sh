#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate

# Run linting
echo "Running Ruff..."
ruff check .

# Run type checking
echo "Running MyPy..."
mypy src/mcp_devops_hub

# Run tests
echo "Running tests..."
pytest tests/