from unittest.mock import patch

import pytest

from mcp_devops_hub.clients.groq_client import GroqClient


@pytest.fixture
def groq_client():
    return GroqClient()

@pytest.mark.asyncio
async def test_analyze_code(groq_client):
    with patch.object(groq_client, 'generate_completion') as mock_generate:
        mock_generate.return_value = "Test analysis result"
        
        result = await groq_client.analyze_code(
            code="def test(): pass",
            language="python"
        )
        
        assert result == "Test analysis result"
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_generate_documentation(groq_client):
    with patch.object(groq_client, 'generate_completion') as mock_generate:
        mock_generate.return_value = "Test documentation"
        
        result = await groq_client.generate_documentation(
            code="def test(): pass",
            language="python"
        )
        
        assert result == "Test documentation"
        mock_generate.assert_called_once()