from typing import Any

import groq

from ..config import settings
from ..utilities.logging import get_logger

logger = get_logger(__name__)

class GroqClient:
    """Client for interacting with Groq's API."""
    
    def __init__(self):
        self.client = groq.Groq(
            api_key=settings.groq_api_key.get_secret_value(),
        )
        self.model = settings.groq_model_name
        self.max_tokens = settings.groq_max_tokens
        self.temperature = settings.groq_temperature

    async def generate_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any
    ) -> str:
        """
        Generate a completion using Groq's API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            The generated text response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating Groq completion: {e}")
            raise

    async def analyze_code(self, code: str, language: str) -> str:
        """
        Analyze code using Groq's API.
        
        Args:
            code: The code to analyze
            language: The programming language
        
        Returns:
            Analysis results as text
        """
        messages = [
            {
                "role": "system",
                "content": "You are a code analysis expert. Analyze the provided code for quality, potential issues, and suggestions for improvement."
            },
            {
                "role": "user",
                "content": f"Please analyze this {language} code:\n\n{code}"
            }
        ]
        
        return await self.generate_completion(messages, temperature=0.3)

    async def generate_documentation(self, code: str, language: str) -> str:
        """
        Generate documentation for code using Groq's API.
        
        Args:
            code: The code to document
            language: The programming language
        
        Returns:
            Generated documentation as text
        """
        messages = [
            {
                "role": "system",
                "content": "You are a technical documentation expert. Generate clear and comprehensive documentation for the provided code."
            },
            {
                "role": "user",
                "content": f"Please generate documentation for this {language} code:\n\n{code}"
            }
        ]
        
        return await self.generate_completion(messages, temperature=0.2)