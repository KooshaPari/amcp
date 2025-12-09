"""Tests for Voyage AI models and enums."""

import pytest
from datetime import datetime, timezone
from services.embeddings import (
    VoyageModel,
    InputType,
    EmbeddingResult,
    BatchEmbeddingResult,
    RerankResult,
)


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class TestVoyageModel:
    """Test Voyage model enum."""

    def test_model_values(self):
        """Test voyage model values."""
        assert VoyageModel.VOYAGE_3.value == "voyage-3"
        assert VoyageModel.VOYAGE_3_LITE.value == "voyage-3-lite"
        assert VoyageModel.VOYAGE_CODE_3.value == "voyage-code-3"
        assert VoyageModel.VOYAGE_FINANCE_2.value == "voyage-finance-2"
        assert VoyageModel.VOYAGE_LAW_2.value == "voyage-law-2"
        assert VoyageModel.VOYAGE_MULTILINGUAL_2.value == "voyage-multilingual-2"

    def test_model_string_conversion(self):
        """Test model string conversion."""
        model = VoyageModel.VOYAGE_3
        assert str(model) == "VoyageModel.VOYAGE_3"
        assert model.value == "voyage-3"


class TestInputType:
    """Test input type enum."""

    def test_input_type_values(self):
        """Test input type values."""
        assert InputType.QUERY.value == "query"
        assert InputType.DOCUMENT.value == "document"


class TestEmbeddingResult:
    """Test embedding result model."""

    def test_embedding_result_creation(self):
        """Test embedding result creation."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = EmbeddingResult(
            embedding=embedding,
            text="test text",
            model="voyage-3",
            input_type="document",
            usage={"total_tokens": 10}
        )

        assert len(result.embedding) == 5
        assert result.model == "voyage-3"
        assert result.text == "test text"
        assert result.input_type == "document"
        assert result.usage["total_tokens"] == 10

    def test_embedding_result_dimensions(self):
        """Test embedding dimensions property."""
        result = EmbeddingResult(
            embedding=[0.1, 0.2, 0.3, 0.4],
            text="test",
            model="voyage-3",
            input_type="query",
            usage={"total_tokens": 5}
        )

        assert result.dimensions == 4

    def test_embedding_result_cached(self):
        """Test embedding result cached flag."""
        result = EmbeddingResult(
            embedding=[0.1, 0.2],
            text="test",
            model="voyage-3",
            input_type=None,
            usage={"total_tokens": 5},
            cached=True
        )

        assert result.cached is True

    def test_embedding_result_defaults(self):
        """Test embedding result default values."""
        result = EmbeddingResult(
            embedding=[0.1],
            text="x",
            model="voyage-3",
            input_type=None,
            usage={}
        )

        assert result.cached is False


class TestBatchEmbeddingResult:
    """Test batch embedding result model."""

    def test_batch_result_creation(self):
        """Test batch result creation."""
        results = [
            EmbeddingResult(
                embedding=[0.1, 0.2],
                text="a",
                model="voyage-3",
                input_type=None,
                usage={"total_tokens": 5}
            ),
            EmbeddingResult(
                embedding=[0.3, 0.4],
                text="b",
                model="voyage-3",
                input_type=None,
                usage={"total_tokens": 5}
            ),
        ]
        batch = BatchEmbeddingResult(
            embeddings=results,
            model="voyage-3",
            total_tokens=10,
            processing_time_ms=50.5
        )

        assert len(batch.embeddings) == 2
        assert batch.total_tokens == 10
        assert batch.processing_time_ms == 50.5

    def test_batch_result_model(self):
        """Test batch result model attribute."""
        batch = BatchEmbeddingResult(
            embeddings=[
                EmbeddingResult(
                    embedding=[0.1],
                    text="x",
                    model="voyage-3",
                    input_type=None,
                    usage={}
                )
            ],
            model="voyage-3",
            total_tokens=5,
            processing_time_ms=10.0
        )

        assert batch.model == "voyage-3"


class TestRerankResult:
    """Test rerank result model."""

    def test_rerank_result_creation(self):
        """Test rerank result creation."""
        result = RerankResult(
            index=0,
            document="Test document",
            relevance_score=0.95
        )

        assert result.index == 0
        assert result.relevance_score == 0.95

    def test_rerank_result_comparison(self):
        """Test rerank results can be sorted by score."""
        results = [
            RerankResult(index=0, document="Doc 1", relevance_score=0.7),
            RerankResult(index=1, document="Doc 2", relevance_score=0.9),
            RerankResult(index=2, document="Doc 3", relevance_score=0.8),
        ]

        sorted_results = sorted(results, key=lambda r: r.relevance_score, reverse=True)
        assert sorted_results[0].relevance_score == 0.9
