import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from ..utilities.logging import get_logger
from .github_client import GitHubClient
from .groq_client import GroqClient
from .jenkins_client import JenkinsClient
from .jira_client import JiraClient

logger = get_logger(__name__)

@dataclass
class Clients:
    """Holds initialized API client instances."""
    jira: JiraClient | None = field(default=None)
    github: GitHubClient | None = field(default=None)
    jenkins: JenkinsClient | None = field(default=None)
    groq: GroqClient | None = field(default=None)
    # Add other clients like Slack, Teams here if implemented

@asynccontextmanager
async def create_api_clients() -> AsyncIterator[Clients]:
    """
    Async context manager to initialize and clean up API clients.
    Yields a Clients object containing the initialized instances.
    """
    logger.info("Initializing API clients...")
    clients = Clients()
    try:
        # Initialize clients concurrently
        init_tasks = {
            "jira": asyncio.create_task(asyncio.to_thread(JiraClient)),
            "github": asyncio.create_task(asyncio.to_thread(GitHubClient)),
            "jenkins": asyncio.create_task(asyncio.to_thread(JenkinsClient)),
            "groq": asyncio.create_task(asyncio.to_thread(GroqClient)),
            # Add tasks for other clients
        }

        results = await asyncio.gather(*init_tasks.values(), return_exceptions=True)

        # Assign results or log errors
        client_map = {
            "jira": JiraClient, "github": GitHubClient,
            "jenkins": JenkinsClient, "groq": GroqClient
        }
        initialized_clients = {}

        for i, name in enumerate(init_tasks.keys()):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to initialize {name.capitalize()} client: {result}")
            elif isinstance(result, client_map[name]):
                 initialized_clients[name] = result
                 logger.info(f"{name.capitalize()} client ready.")
            else:
                 logger.error(f"Unexpected result type during {name.capitalize()} client initialization: {type(result)}")


        clients = Clients(**initialized_clients)

        yield clients

    finally:
        logger.info("Closing API clients...")
        close_tasks = []
        if clients.jira:
            close_tasks.append(asyncio.create_task(clients.jira.close()))
        if clients.github:
            close_tasks.append(asyncio.create_task(clients.github.close()))
        if clients.jenkins:
            close_tasks.append(asyncio.create_task(clients.jenkins.close()))
        # Add close tasks for other clients (Groq doesn't need explicit close)

        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
            logger.info("Finished closing API clients.")
        else:
            logger.info("No active clients needed closing.")

# Export for easy import
__all__ = ["Clients", "GitHubClient", "GroqClient", "JenkinsClient", "JiraClient", "create_api_clients"]
