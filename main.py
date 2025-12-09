"""
Main Application - SmartCP MCP Frontend

FastAPI application delegating to Bifrost backend via GraphQL.
SmartCP handles MCP protocol; Bifrost handles business logic.
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from smartcp.infrastructure.bifrost import BifrostClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Bifrost client (initialized on startup)
bifrost_client: Optional[BifrostClient] = None


# ============================================================================
# Lifespan Events
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    global bifrost_client
    logger.info("Starting SmartCP MCP Frontend")
    try:
        # Initialize Bifrost client
        bifrost_client = BifrostClient()
        await bifrost_client.connect()
        logger.info("Connected to Bifrost backend")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info("Shutting down SmartCP")
    try:
        if bifrost_client:
            await bifrost_client.disconnect()
            logger.info("Disconnected from Bifrost backend")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="SmartCP - MCP Frontend",
    description="MCP protocol frontend delegating to Bifrost backend",
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================================
# Request/Response models
# ============================================================================
class RoutingRequest(BaseModel):
    """Routing request"""
    action: str
    prompt: str
    context: Optional[dict] = None


class RoutingResponse(BaseModel):
    """Routing response"""
    route: str
    tools: List[str]
    cli_command: str
    hooks: List[str]
    confidence: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    databases: dict


# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    global bifrost_client
    try:
        # Check Bifrost connection
        bifrost_status = "connected" if bifrost_client and bifrost_client.is_connected else "disconnected"

        return HealthResponse(
            status="healthy" if bifrost_status == "connected" else "degraded",
            databases={"bifrost": bifrost_status}
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/route", response_model=RoutingResponse)
async def route_query(request: RoutingRequest):
    """
    Route a query to appropriate tools via Bifrost.

    Args:
        request: Routing request with action and prompt

    Returns:
        RoutingResponse with selected route and tools
    """
    global bifrost_client

    if not bifrost_client:
        raise HTTPException(status_code=503, detail="Bifrost client not initialized")

    try:
        # Delegate routing to Bifrost
        decision = await bifrost_client.route_request(
            prompt=request.prompt,
            context=request.context or {}
        )

        return RoutingResponse(
            route=decision.selected_tool,
            tools=[decision.selected_tool],
            cli_command=f"execute {decision.selected_tool}",
            hooks=[],
            confidence=decision.confidence
        )

    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tools")
async def list_tools():
    """List all available tools from Bifrost"""
    global bifrost_client

    if not bifrost_client:
        raise HTTPException(status_code=503, detail="Bifrost client not initialized")

    try:
        tools = await bifrost_client.query_tools()
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "tags": t.tags
                }
                for t in tools
            ],
            "count": len(tools),
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get details for a specific tool"""
    global bifrost_client

    if not bifrost_client:
        raise HTTPException(status_code=503, detail="Bifrost client not initialized")

    try:
        tool = await bifrost_client.query_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "category": tool.category,
            "tags": tool.tags
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/semantic")
async def semantic_search(query: str, limit: int = 10):
    """
    Semantic search via Bifrost.

    Args:
        query: Search query
        limit: Number of results

    Returns:
        List of search results
    """
    global bifrost_client

    if not bifrost_client:
        raise HTTPException(status_code=503, detail="Bifrost client not initialized")

    try:
        results = await bifrost_client.semantic_search(
            query=query,
            limit=limit
        )

        return {
            "query": query,
            "results": [
                {
                    "id": r.id,
                    "content": r.content,
                    "metadata": r.metadata,
                    "score": r.score
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

