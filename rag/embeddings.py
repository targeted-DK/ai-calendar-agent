from typing import List
import openai
import requests
from config import settings


class EmbeddingGenerator:
    """Generate embeddings for text using OpenAI or Ollama embedding models."""

    def __init__(self, provider: str = None):
        """
        Initialize embedding generator.

        Args:
            provider: 'openai' or 'ollama'. If None, uses LLM_PROVIDER from settings.
        """
        self.provider = provider or settings.llm_provider

        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.model = settings.embedding_model
        elif self.provider == "ollama":
            self.ollama_url = settings.ollama_base_url
            self.model = "nomic-embed-text"
        else:
            # Default to Ollama for local operation
            self.provider = "ollama"
            self.ollama_url = settings.ollama_base_url
            self.model = "nomic-embed-text"

    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

    def _generate_ollama_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama local model."""
        response = requests.post(
            f"{self.ollama_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text
            }
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of embedding values
        """
        if self.provider == "openai":
            return self._generate_openai_embedding(text)
        else:
            return self._generate_ollama_embedding(text)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        if self.provider == "openai":
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        else:
            # Ollama doesn't support batch, so process one at a time
            return [self._generate_ollama_embedding(text) for text in texts]
