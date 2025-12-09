"""
Factory for creating and managing inference engine singleton.
"""

import os
from typing import Optional

from .orchestrator import ComprehensiveScopeInferenceEngine


# Global singleton
_inference_engine: Optional[ComprehensiveScopeInferenceEngine] = None


def get_comprehensive_inference_engine(
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None,
    redis_url: Optional[str] = None,
) -> ComprehensiveScopeInferenceEngine:
    """Get or create global comprehensive inference engine."""
    global _inference_engine

    if _inference_engine is None:
        # Load from environment
        uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = neo4j_user or os.getenv("NEO4J_USERNAME", "neo4j")
        password = neo4j_password or os.getenv("NEO4J_PASSWORD", "")
        redis = redis_url or os.getenv(
            "UPSTASH_REDIS_REST_URL", "redis://localhost:6379"
        )

        _inference_engine = ComprehensiveScopeInferenceEngine(
            neo4j_uri=uri,
            neo4j_user=user,
            neo4j_password=password,
            redis_url=redis,
        )

    return _inference_engine
