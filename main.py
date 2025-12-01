"""
Main Application - Semantic Tool Router

FastAPI application for semantic tool routing with auto-discovery.
"""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from router import ArchRouter, ToolRegistry, TOOL_REGISTRY
from services import DatabaseService, SearchService
from services.database import DatabaseConfig
from hooks.semantic_discovery import pre_discovery_hook
from infrastructure.db_init import init_database
from infrastructure.mlx_integration import MLXModelManager, EmbeddingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Semantic Tool Router",
    description="Intelligent tool routing with auto-discovery",
    version="1.0.0",
)

# Initialize components
router = ArchRouter()
registry = ToolRegistry(TOOL_REGISTRY)
mlx_manager = MLXModelManager()
embedding_manager = EmbeddingManager()

# Database config (from environment)
db_config = DatabaseConfig(
    postgres_url="postgresql://mcp_user:mcp_password@localhost/mcp_db",
    memgraph_url="bolt://localhost:7687",
    qdrant_url="http://localhost:6333",
    valkey_url="redis://localhost:6379",
)
db_service = DatabaseService(db_config)
search_service = SearchService(db_service)


# Request/Response models
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


# Lifecycle events
@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    logger.info("Starting Semantic Tool Router")
    try:
        # Connect to databases
        await db_service.connect()
        logger.info("Database connections established")

        # Initialize database schema
        if await init_database(db_service):
            logger.info("Database schema initialized")

        # Load MLX model
        mlx_manager.load()
        logger.info("MLX model loaded")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down Semantic Tool Router")
    try:
        await db_service.disconnect()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Shutdown failed: {e}")


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        db_health = await db_service.health_check()
        return HealthResponse(
            status="healthy",
            databases=db_health,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/route", response_model=RoutingResponse)
async def route_query(request: RoutingRequest):
    """
    Route a query to appropriate tools.
    
    Args:
        request: Routing request with action and prompt
    
    Returns:
        RoutingResponse with selected route and tools
    """
    try:
        # Execute pre-discovery hook
        discovery_result = await pre_discovery_hook(
            action=request.action,
            prompt=request.prompt,
            router=router,
            registry=registry,
            context=request.context,
        )
        
        return RoutingResponse(
            route=discovery_result.route,
            tools=discovery_result.tools,
            cli_command=discovery_result.cli_command,
            hooks=discovery_result.hooks,
            confidence=discovery_result.confidence,
        )
        
    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/routes")
async def list_routes():
    """List all available routes"""
    return {
        "routes": registry.list_routes(),
        "count": len(registry.list_routes()),
    }


@app.get("/tools")
async def list_tools():
    """List all available tools"""
    return {
        "tools": registry.list_all_tools(),
        "count": len(registry.list_all_tools()),
    }


@app.get("/route/{route_name}")
async def get_route(route_name: str):
    """Get details for a specific route"""
    route = registry.get_route(route_name)
    if not route:
        raise HTTPException(status_code=404, detail=f"Route not found: {route_name}")
    return route


@app.post("/search/semantic")
async def semantic_search(query: str, limit: int = 10):
    """
    Semantic search using pgvector.

    Args:
        query: Search query
        limit: Number of results

    Returns:
        List of search results
    """
    try:
        # Generate embedding
        embedding = embedding_manager.generate_embedding(query)

        # Search
        results = await search_service.semantic_search(embedding, limit=limit)

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/search/fulltext")
async def full_text_search(query: str, limit: int = 10):
    """
    Full-text search using PostgreSQL FTS.

    Args:
        query: Search query
        limit: Number of results

    Returns:
        List of search results
    """
    try:
        results = await search_service.full_text_search(query, limit=limit)

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Full-text search failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/search/hybrid")
async def hybrid_search(query: str, limit: int = 10):
    """
    Hybrid search combining FTS and semantic search.

    Args:
        query: Search query
        limit: Number of results

    Returns:
        List of hybrid search results
    """
    try:
        # Generate embedding
        embedding = embedding_manager.generate_embedding(query)

        # Hybrid search
        results = await search_service.hybrid_search(
            query_text=query,
            query_embedding=embedding,
            limit=limit,
        )

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/model/stats")
async def model_stats():
    """Get MLX model statistics"""
    return mlx_manager.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

