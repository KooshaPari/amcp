"""MLX Embedding Service."""
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using MLX."""

    def __init__(self, model_name: str = "mlx-embed"):
        """Initialize embedding service."""
        self.model_name = model_name
        self.model = None
        self.dimension = 768  # Standard embedding dimension

    async def initialize(self) -> bool:
        """Initialize MLX model."""
        try:
            logger.info(f"Initializing embedding model: {self.model_name}")

            # TODO: Load actual MLX model when available
            # from mlx_lm import load
            # self.model = load(self.model_name)

            logger.info("Embedding model initialized (mock)")
            return True

        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            return False

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            if self.model is None:
                await self.initialize()

            # Mock embeddings for now
            # In production, use actual MLX model
            # embeddings = self.model.encode(texts)

            # Generate mock embeddings (normalized random vectors)
            embeddings = []
            for text in texts:
                # Use text hash for deterministic mock embeddings
                np.random.seed(hash(text) % (2**32))
                vec = np.random.randn(self.dimension)
                vec = vec / np.linalg.norm(vec)  # Normalize
                embeddings.append(vec.tolist())

            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
