import pytest
from unittest.mock import patch, MagicMock

from mcp_devops_hub.clients.github_client import GitHubClient
from mcp_devops_hub.utilities import HTTP_NOT_FOUND

@pytest.fixture
def mock_github():
    """Create a mock GitHub client for testing."""
    with patch('mcp_devops_hub.clients.github_client.Github') as mock_github:
        # Mock the user object
        mock_user = MagicMock()
        mock_user.login = "test-user"
        mock_github.return_value.get_user.return_value = mock_user
        
        yield mock_github

@pytest.mark.asyncio
async def test_github_client_initialization(mock_github):
    """Test that the GitHub client initializes correctly."""
    # Mock the settings
    with patch('mcp_devops_hub.clients.github_client.settings') as mock_settings:
        # Create a mock SecretStr for the token
        mock_token = MagicMock()
        mock_token.get_secret_value.return_value = "test-token"
        mock_settings.github_token = mock_token
        mock_settings.github_base_url = None
        
        # Initialize the client
        client = GitHubClient()
        
        # Check that the client was initialized correctly
        assert client._client is not None
        mock_github.assert_called_once_with(login_or_token="test-token", base_url=mock_github.return_value.NotSet)
        mock_github.return_value.get_user.assert_called_once()

@pytest.mark.asyncio
async def test_get_repo_success():
    """Test successful repository retrieval."""
    # Create a mock client
    client = GitHubClient()
    
    # Mock the _run_sync method
    mock_repo = MagicMock()
    client._run_sync = MagicMock()
    client._run_sync.return_value = mock_repo
    client._client = MagicMock()  # Ensure _client is not None
    
    # Call the method
    repo = await client.get_repo("owner", "repo")
    
    # Check the result
    assert repo is mock_repo
    client._run_sync.assert_called_once()

@pytest.mark.asyncio
async def test_get_repo_not_found():
    """Test repository not found handling."""
    # Create a mock client
    client = GitHubClient()
    client._client = MagicMock()  # Ensure _client is not None
    
    # Mock the _run_sync method to raise a GithubException with 404 status
    from github import GithubException
    exception = GithubException(HTTP_NOT_FOUND, {"message": "Not Found"})
    client._run_sync = MagicMock()
    client._run_sync.side_effect = exception
    
    # Call the method
    repo = await client.get_repo("owner", "repo")
    
    # Check the result
    assert repo is None
