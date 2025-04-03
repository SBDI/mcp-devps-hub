#!/bin/bash
# Run the MCP DevOps Hub client demo

# Activate virtual environment
source .venv/bin/activate

# Run the demo script
python scripts/demo_clients.py

# Wait for user input before closing
read -p "Press Enter to continue..."
