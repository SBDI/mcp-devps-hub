#!/bin/bash
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies using uv
echo "Installing dependencies..."
uv pip install -r requirements-dev.txt

# Install the package in editable mode
echo "Installing package in editable mode..."
uv pip install -e .

echo "Development environment setup complete!"