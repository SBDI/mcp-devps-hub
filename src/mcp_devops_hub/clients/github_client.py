import asyncio
from collections.abc import Callable
from typing import Any

from github import ContentFile, Github, GithubException, Repository
from github.GithubObject import NotSet

from ..config import settings
from ..utilities.logging import get_logger
from ..utilities import HTTP_NOT_FOUND

logger = get_logger(__name__)

class GitHubClient:
    """Asynchronous client for interacting with GitHub."""

    def __init__(self) -> None:
        if not settings.github_token:
            logger.warning("GITHUB_TOKEN not configured. GitHub client disabled.")
            self._client = None
            return

        try:
            # PyGithub is synchronous, wrap calls in asyncio.to_thread
            auth_token = settings.github_token.get_secret_value()
            base_url = settings.github_base_url or NotSet # Use default if None

            self._client = Github(login_or_token=auth_token, base_url=base_url)
            # Test connection by getting the authenticated user
            user = self._client.get_user()
            logger.info(f"GitHub client initialized. Authenticated as: {user.login}")

        except GithubException as e:
            logger.error(f"Failed to initialize GitHub client: {e.status} - {e.data}")
            self._client = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during GitHub client initialization: {e}")
            self._client = None

    async def _run_sync(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Runs a synchronous PyGithub function in a separate thread."""
        if not self._client:
            raise ConnectionError("GitHub client is not initialized or configured.")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def get_repo(self, owner: str, repo_name: str) -> Repository.Repository | None:
        """Gets a repository object."""
        if not self._client:
            return None
        try:
            repo = await self._run_sync(self._client.get_repo, f"{owner}/{repo_name}")
            logger.debug(f"Fetched repository object for {owner}/{repo_name}")
            return repo
        except GithubException as e:
            if e.status == HTTP_NOT_FOUND:
                logger.warning(f"Repository {owner}/{repo_name} not found.")
                return None
            logger.error(f"GitHub API error fetching repo {owner}/{repo_name}: {e.status} - {e.data}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching repo {owner}/{repo_name}: {e}")
            raise

    async def get_content(self, owner: str, repo_name: str, path: str) -> ContentFile.ContentFile | list[ContentFile.ContentFile] | None:
        """Gets the content of a file or directory listing."""
        repo = await self.get_repo(owner, repo_name)
        if not repo:
            return None
        try:
            content = await self._run_sync(repo.get_contents, path)
            logger.info(f"Fetched content for path '{path}' in {owner}/{repo_name}")
            return content
        except GithubException as e:
            if e.status == HTTP_NOT_FOUND:
                logger.warning(f"Path '{path}' not found in {owner}/{repo_name}.")
                return None
            logger.error(f"GitHub API error fetching content for {owner}/{repo_name}/{path}: {e.status} - {e.data}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching content for {owner}/{repo_name}/{path}: {e}")
            raise

    async def close(self):
        """Closes the GitHub client connection (if applicable)."""
        # PyGithub doesn't have an explicit close method for token auth
        logger.debug("GitHub client (token auth) does not require explicit closing.")
        pass
