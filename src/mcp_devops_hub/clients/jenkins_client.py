from typing import Any

import httpx

from ..config import settings
from ..utilities.logging import get_logger

logger = get_logger(__name__)

class JenkinsClient:
    """Asynchronous client for interacting with Jenkins."""

    def __init__(self):
        if not settings.jenkins_url or not settings.jenkins_username or not settings.jenkins_token:
            logger.warning("Jenkins credentials not fully configured. Jenkins client disabled.")
            self._client = None
            self._base_url = None
            return

        self._base_url = settings.jenkins_url.rstrip('/')
        auth = (settings.jenkins_username, settings.jenkins_token.get_secret_value())
        self._client = httpx.AsyncClient(base_url=self._base_url, auth=auth)
        logger.info("Jenkins client initialized.")

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any] | None:
        """Makes an asynchronous request to the Jenkins API."""
        if not self._client:
            raise ConnectionError("Jenkins client is not initialized or configured.")
        url = f"{endpoint}/api/json" # Jenkins standard API suffix
        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Jenkins API error ({e.request.method} {e.request.url}): {e.response.status_code} - {e.response.text}")
            # Optionally return None or re-raise a custom exception
            return None # Or raise specific error
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Jenkins ({e.request.method} {e.request.url}): {e}")
            raise ConnectionError(f"Could not connect to Jenkins: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during Jenkins request: {e}")
            raise

    async def get_build_info(self, job_name: str, build_number: str) -> dict[str, Any] | None:
        """Gets information about a specific build."""
        # Jenkins job paths can be nested, handle simple case for now
        # A more robust solution would handle folder structures.
        endpoint = f"/job/{job_name}/{build_number}"
        logger.debug(f"Fetching build info from Jenkins endpoint: {endpoint}")
        return await self._request("GET", endpoint)

    async def get_job_info(self, job_name: str) -> dict[str, Any] | None:
        """Gets information about a specific job."""
        endpoint = f"/job/{job_name}"
        logger.debug(f"Fetching job info from Jenkins endpoint: {endpoint}")
        return await self._request("GET", endpoint)

    async def close(self):
        """Closes the underlying HTTPX client."""
        if self._client:
            await self._client.aclose()
            logger.info("Jenkins client closed.")
