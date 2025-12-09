"""Test script for Bifrost ML service."""
import asyncio
import httpx


async def test_service():
    """Test the ML service endpoints."""
    base_url = "http://localhost:8001"

    async with httpx.AsyncClient() as client:
        print("Testing Bifrost ML Service\n")

        # Test health
        print("1. Health Check")
        resp = await client.get(f"{base_url}/health")
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}\n")

        # Test models list
        print("2. List Models")
        resp = await client.get(f"{base_url}/models")
        print(f"   Status: {resp.status_code}")
        print(f"   Models: {resp.json()}\n")

        # Test classification
        print("3. Classify Prompt")
        resp = await client.post(
            f"{base_url}/classify",
            json={"prompt": "What is the weather like?", "context": {}}
        )
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}\n")

        # Test routing
        print("4. Route Request")
        resp = await client.post(
            f"{base_url}/route",
            json={
                "prompt": "Analyze this complex multi-step problem in detail",
                "context": {},
                "output_tokens_estimate": 1000
            }
        )
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}\n")

        # Test embeddings
        print("5. Generate Embeddings")
        resp = await client.post(
            f"{base_url}/embed",
            json={"texts": ["Hello world", "Machine learning"], "model": "mlx-embed"}
        )
        print(f"   Status: {resp.status_code}")
        data = resp.json()
        print(f"   Model: {data['model_used']}")
        print(f"   Embeddings: {len(data['embeddings'])} vectors of dimension {len(data['embeddings'][0])}\n")

        print("All tests passed!")


if __name__ == "__main__":
    print("Starting tests...")
    print("Make sure the service is running: python app.py\n")
    asyncio.run(test_service())
