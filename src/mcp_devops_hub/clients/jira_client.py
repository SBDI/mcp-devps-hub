import asyncio

from jira import JIRA, Issue
from jira.exceptions import JIRAError
from jira.resources import Sprint  # Attempt to import Sprint from resources

from ..config import settings
from ..utilities.logging import get_logger
from ..utilities import HTTP_NOT_FOUND

logger = get_logger(__name__)


class JiraClient:
    """Asynchronous client for interacting with Jira."""

    def __init__(self):
        if not settings.jira_url or not settings.jira_username or not settings.jira_api_token:
            logger.warning("Jira credentials not fully configured. Jira client disabled.")
            self._client = None
            return

        try:
            # Note: The 'jira' library is synchronous. We wrap calls in asyncio.to_thread.
            self._client = JIRA(
                server=settings.jira_url,
                basic_auth=(settings.jira_username, settings.jira_api_token.get_secret_value()),
            )
            logger.info("Jira client initialized.")
        except JIRAError as e:
            logger.error(f"Failed to initialize Jira client: {e.status_code} - {e.text}")
            self._client = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Jira client initialization: {e}")
            self._client = None

    async def _run_sync(self, func, *args, **kwargs):
        """Runs a synchronous Jira library function in a separate thread."""
        if not self._client:
            raise ConnectionError("Jira client is not initialized or configured.")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def get_sprint_tasks(self, project_key: str, sprint_id: str) -> list[Issue]:
        """Gets all tasks for a specific sprint."""
        if not self._client:
            return []
        try:
            # JQL to find issues in the specified sprint for the given project
            jql = f'project = "{project_key}" AND sprint = {sprint_id}'
            logger.debug(f"Executing JQL: {jql}")
            # The 'jira' library handles pagination internally by default with search_issues
            tasks = await self._run_sync(
                self._client.search_issues, jql, maxResults=False
            )  # maxResults=False fetches all
            logger.info(
                f"Found {len(tasks)} tasks for sprint {sprint_id} in project {project_key}."
            )
            return tasks
        except JIRAError as e:
            logger.error(
                f"Jira API error fetching sprint tasks ({project_key}, {sprint_id}): {e.status_code} - {e.text}"
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching sprint tasks: {e}")
            raise

    async def get_sprint(self, sprint_id: int) -> Sprint | None:
        """Gets details for a specific sprint by its ID."""
        if not self._client:
            return None
        try:
            sprint = await self._run_sync(self._client.sprint, sprint_id)
            logger.info(f"Fetched details for sprint {sprint_id}.")
            return sprint
        except JIRAError as e:
            # Handle 404 Not Found specifically
            if e.status_code == HTTP_NOT_FOUND:
                logger.warning(f"Sprint with ID {sprint_id} not found.")
                return None
            logger.error(f"Jira API error fetching sprint {sprint_id}: {e.status_code} - {e.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching sprint {sprint_id}: {e}")
            raise

    async def get_completed_sprints(self, project_key: str, limit: int = 5) -> list[Sprint]:
        """Gets the most recently completed sprints for a project."""
        if not self._client:
            return []
        try:
            # Assuming board ID 1 - this might need configuration or dynamic lookup
            # A more robust approach would find the board associated with the project_key
            board_id = 1  # TODO: Make board ID configurable or discoverable
            logger.warning(f"Using hardcoded board_id={board_id} for project {project_key}")
            sprints = await self._run_sync(
                self._client.sprints, board_id, state="closed", maxResults=limit
            )
            # The API might return sprints from multiple projects if board isn't specific
            # Filter sprints relevant to the project_key if possible (originBoardId might help)
            # For now, we assume the board is specific enough or filtering happens later
            logger.info(
                f"Found {len(sprints)} completed sprints for board {board_id} (limit {limit})."
            )
            return sprints
        except JIRAError as e:
            logger.error(
                f"Jira API error fetching completed sprints for board {board_id}: {e.status_code} - {e.text}"
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching completed sprints: {e}")
            raise

    async def close(self):
        """Closes the Jira client connection (if applicable)."""
        if self._client:
            try:
                # The standard JIRA client doesn't have an explicit close method for basic auth
                # If using OAuth or session-based auth, close logic would go here.
                await self._run_sync(self._client.close)  # Standard client might not have close()
                logger.info("Jira client closed (if applicable).")
            except AttributeError:
                logger.debug("Jira client (basic auth) does not require explicit closing.")
            except Exception as e:
                logger.error(f"Error closing Jira client: {e}")
