import logging
import sys

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr, # Log to stderr by default
)

def get_logger(name: str) -> logging.Logger:
    """Gets a logger instance with the specified name."""
    return logging.getLogger(name)

# Example: Configure a specific logger's level if needed
# get_logger("mcp_devops_hub.clients.jira_client").setLevel(logging.DEBUG)
