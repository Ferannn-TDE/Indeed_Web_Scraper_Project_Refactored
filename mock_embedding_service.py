# mock_embedding_service.py

from main import IEmbeddingService

class MockEmbeddingService(IEmbeddingService):
    """Mock version of the embedding service for unit testing."""

    def get_embedding(self, text: str):
        # Return deterministic fake vector
        return [1.0, 0.0, 0.0]

    def get_embeddings_batch(self, texts: list):
        # Return one fake vector per text
        return [[1.0, 0.0, 0.0] for _ in texts]
