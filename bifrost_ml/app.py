"""
Bifrost ML Microservice

FastAPI + gRPC server for ML inference operations:
- Prompt classification
- Model routing
- Embedding generation
"""
import asyncio
import logging
import time
from concurrent import futures
from typing import Dict, Any

import grpc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import generated gRPC code (will be generated from proto)
# from proto import ml_service_pb2, ml_service_pb2_grpc

# Import services
from services.routing import get_routing_service
from services.classification import get_unified_classifier
from services.embeddings import get_embedding_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Bifrost ML Service",
    description="ML inference microservice for routing and classification",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track uptime
START_TIME = time.time()


# ============================================================================
# Pydantic Models
# ============================================================================

class ClassifyRequest(BaseModel):
    """Request for prompt classification."""
    prompt: str = Field(..., description="User prompt to classify")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional context")


class ClassifyResponse(BaseModel):
    """Response from classification."""
    complexity: str = Field(..., description="Complexity level")
    confidence: float = Field(..., description="Confidence score")
    tool_name: str = Field(..., description="Predicted tool name")
    alternatives: list[Dict[str, float]] = Field(
        default_factory=list,
        description="Alternative predictions"
    )


class EmbedRequest(BaseModel):
    """Request for embedding generation."""
    texts: list[str] = Field(..., description="Texts to embed")
    model: str = Field(default="mlx-embed", description="Model to use")


class EmbedResponse(BaseModel):
    """Response from embedding."""
    embeddings: list[list[float]] = Field(..., description="Generated embeddings")
    model_used: str = Field(..., description="Model used for embeddings")


class RouteRequest(BaseModel):
    """Request for model routing."""
    prompt: str = Field(..., description="User prompt")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional context")
    output_tokens_estimate: int = Field(1000, description="Estimated output tokens")


class RouteResponse(BaseModel):
    """Response from routing."""
    model: str = Field(..., description="Selected model")
    complexity: str = Field(..., description="Task complexity")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    estimated_latency_ms: int = Field(..., description="Estimated latency in ms")
    rationale: str = Field(..., description="Routing rationale")
    fallback_model: str | None = Field(None, description="Fallback model")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime_seconds: int = Field(..., description="Uptime in seconds")


# ============================================================================
# FastAPI Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = int(time.time() - START_TIME)
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime
    )


@app.post("/classify", response_model=ClassifyResponse)
async def classify_prompt(request: ClassifyRequest):
    """Classify a prompt to determine complexity and tool."""
    try:
        classifier = get_unified_classifier()
        prediction = await classifier.classify(request.prompt, request.context)

        return ClassifyResponse(
            complexity="moderate",  # From router
            confidence=prediction.confidence,
            tool_name=prediction.tool_name,
            alternatives=[
                {"name": name, "score": score}
                for name, score in prediction.alternatives
            ]
        )
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed", response_model=EmbedResponse)
async def generate_embeddings(request: EmbedRequest):
    """Generate embeddings for texts."""
    try:
        service = get_embedding_service()
        embeddings = await service.embed_batch(request.texts)

        return EmbedResponse(
            embeddings=embeddings,
            model_used=request.model
        )
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/route", response_model=RouteResponse)
async def route_request(request: RouteRequest):
    """Route request to optimal model."""
    try:
        service = get_routing_service()
        decision = await service.route(
            request.prompt,
            request.context,
            request.output_tokens_estimate
        )

        return RouteResponse(
            model=decision.model,
            complexity=decision.complexity.value,
            estimated_cost_usd=decision.estimated_cost_usd,
            estimated_latency_ms=decision.estimated_latency_ms,
            rationale=decision.rationale,
            fallback_model=decision.fallback_model
        )
    except Exception as e:
        logger.error(f"Routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """List available models."""
    try:
        service = get_routing_service()
        models = service.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# gRPC Server (Placeholder - requires generated proto code)
# ============================================================================

class MLServiceServicer:
    """gRPC servicer for ML operations."""

    async def Classify(self, request, context):
        """Classify prompt."""
        # TODO: Implement after proto compilation
        pass

    async def Embed(self, request, context):
        """Generate embeddings."""
        # TODO: Implement after proto compilation
        pass

    async def Route(self, request, context):
        """Route request."""
        # TODO: Implement after proto compilation
        pass

    async def HealthCheck(self, request, context):
        """Health check."""
        # TODO: Implement after proto compilation
        pass


async def serve_grpc():
    """Start gRPC server."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    # ml_service_pb2_grpc.add_MLServiceServicer_to_server(MLServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    logger.info("gRPC server starting on :50051")
    await server.start()
    await server.wait_for_termination()


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Bifrost ML service...")

    # Initialize services
    classifier = get_unified_classifier()
    await classifier.initialize()

    embedding_service = get_embedding_service()
    await embedding_service.initialize()

    # Start gRPC server in background
    # asyncio.create_task(serve_grpc())

    logger.info("Bifrost ML service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Bifrost ML service...")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Bifrost ML service on :8001")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
