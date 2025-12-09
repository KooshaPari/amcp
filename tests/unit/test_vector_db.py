import pytest
from unittest.mock import AsyncMock

from smartcp.infrastructure.adapters.vector_db import VectorDatabase, VectorRecord


@pytest.mark.asyncio
async def test_vector_search_delegates_to_bifrost():
    mock_client = AsyncMock()
    mock_client.query.return_value = {
        "vectorSearch": [
            {"id": "1", "content": "hello", "metadata": {"k": "v"}, "score": 0.9}
        ]
    }

    db = VectorDatabase(bifrost_client=mock_client, use_memory=False)

    results = await db.search_vectors([0.1, 0.2], top_k=5)

    mock_client.query.assert_awaited()
    assert results[0].id == "1"
    assert results[0].metadata["k"] == "v"


@pytest.mark.asyncio
async def test_vector_insert_uses_bifrost_mutation():
    mock_client = AsyncMock()
    mock_client.mutate.return_value = {"upsertVector": {"id": "v1"}}

    db = VectorDatabase(bifrost_client=mock_client, use_memory=False)

    record = VectorRecord(id="v1", vector=[0.1], metadata={"a": 1})
    ok = await db.insert_vector(record)

    mock_client.mutate.assert_awaited()
    assert ok is True
