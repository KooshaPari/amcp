"""
Advanced Discovery System for SmartCP

Provides:
- Full-Text Search (FTS)
- BM25 ranking
- RAG (Retrieval-Augmented Generation)
- Semantic search (existing)
- Hybrid search
"""

import logging
import sqlite3
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Search types."""
    SEMANTIC = "semantic"
    FTS = "fts"
    BM25 = "bm25"
    HYBRID = "hybrid"
    RAG = "rag"


@dataclass
class SearchResult:
    """Search result."""
    id: str
    title: str
    content: str
    score: float
    search_type: SearchType
    metadata: Dict[str, Any] = None


class FullTextSearch:
    """Full-Text Search implementation."""
    
    def __init__(self, db_path: str = "smartcp_fts.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_fts()
    
    def _init_fts(self) -> None:
        """Initialize FTS table."""
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts 
            USING fts5(id, title, content)
        """)
        self.conn.commit()
        logger.info("FTS initialized")
    
    async def index(self, doc_id: str, title: str, content: str) -> None:
        """Index document."""
        try:
            self.conn.execute(
                "INSERT INTO documents_fts VALUES (?, ?, ?)",
                (doc_id, title, content)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
    
    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search documents."""
        try:
            cursor = self.conn.execute("""
                SELECT id, title, content, rank FROM documents_fts
                WHERE documents_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(SearchResult(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    score=abs(row[3]),  # FTS rank is negative
                    search_type=SearchType.FTS
                ))
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []


class BM25Ranker:
    """BM25 ranking algorithm."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.idf_cache: Dict[str, float] = {}
    
    async def index(self, doc_id: str, title: str, content: str) -> None:
        """Index document for BM25."""
        tokens = self._tokenize(f"{title} {content}")
        self.documents[doc_id] = {
            "title": title,
            "content": content,
            "tokens": tokens,
            "length": len(tokens)
        }
        self._update_idf()
    
    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search using BM25."""
        query_tokens = self._tokenize(query)
        scores = {}
        
        avg_doc_length = sum(doc["length"] for doc in self.documents.values()) / len(self.documents) if self.documents else 0
        
        for doc_id, doc in self.documents.items():
            score = 0.0
            for token in query_tokens:
                idf = self.idf_cache.get(token, 0)
                freq = doc["tokens"].count(token)
                
                if freq > 0:
                    numerator = freq * (self.k1 + 1)
                    denominator = freq + self.k1 * (1 - self.b + self.b * (doc["length"] / avg_doc_length))
                    score += idf * (numerator / denominator)
            
            if score > 0:
                scores[doc_id] = score
        
        # Sort by score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        results = []
        for doc_id, score in sorted_docs:
            doc = self.documents[doc_id]
            results.append(SearchResult(
                id=doc_id,
                title=doc["title"],
                content=doc["content"],
                score=score,
                search_type=SearchType.BM25
            ))
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text."""
        return text.lower().split()
    
    def _update_idf(self) -> None:
        """Update IDF cache."""
        total_docs = len(self.documents)
        if total_docs == 0:
            return
        
        token_doc_count: Dict[str, int] = {}
        for doc in self.documents.values():
            for token in set(doc["tokens"]):
                token_doc_count[token] = token_doc_count.get(token, 0) + 1
        
        for token, count in token_doc_count.items():
            self.idf_cache[token] = math.log((total_docs - count + 0.5) / (count + 0.5) + 1)


class RAGSystem:
    """Retrieval-Augmented Generation system."""
    
    def __init__(self, fts: FullTextSearch, bm25: BM25Ranker):
        self.fts = fts
        self.bm25 = bm25
        self.retrieval_cache: Dict[str, List[SearchResult]] = {}
    
    async def retrieve(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Retrieve relevant documents."""
        # Check cache
        if query in self.retrieval_cache:
            return self.retrieval_cache[query]
        
        # Hybrid search: FTS + BM25
        fts_results = await self.fts.search(query, limit)
        bm25_results = await self.bm25.search(query, limit)
        
        # Merge and deduplicate
        merged = {}
        for result in fts_results:
            merged[result.id] = result
        for result in bm25_results:
            if result.id not in merged:
                merged[result.id] = result
        
        results = list(merged.values())[:limit]
        self.retrieval_cache[query] = results
        
        return results
    
    async def augment(self, query: str, context: str) -> str:
        """Augment query with retrieved context."""
        results = await self.retrieve(query)
        
        augmented = f"Query: {query}\n\nContext:\n"
        for result in results:
            augmented += f"- {result.title}: {result.content[:200]}...\n"
        
        augmented += f"\nOriginal Context: {context}"
        return augmented


class AdvancedDiscovery:
    """Unified advanced discovery system."""
    
    def __init__(self, db_path: str = "smartcp_discovery.db"):
        self.fts = FullTextSearch(db_path)
        self.bm25 = BM25Ranker()
        self.rag = RAGSystem(self.fts, self.bm25)
    
    async def index_document(self, doc_id: str, title: str, content: str) -> None:
        """Index document in all systems."""
        await self.fts.index(doc_id, title, content)
        await self.bm25.index(doc_id, title, content)
        logger.info(f"Document indexed: {doc_id}")
    
    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.HYBRID,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search using specified method."""
        if search_type == SearchType.FTS:
            return await self.fts.search(query, limit)
        elif search_type == SearchType.BM25:
            return await self.bm25.search(query, limit)
        elif search_type == SearchType.HYBRID:
            fts_results = await self.fts.search(query, limit)
            bm25_results = await self.bm25.search(query, limit)
            
            # Merge results
            merged = {}
            for result in fts_results:
                merged[result.id] = result
            for result in bm25_results:
                if result.id in merged:
                    merged[result.id].score = (merged[result.id].score + result.score) / 2
                else:
                    merged[result.id] = result
            
            return sorted(merged.values(), key=lambda x: x.score, reverse=True)[:limit]
        elif search_type == SearchType.RAG:
            return await self.rag.retrieve(query, limit)
        
        return []


# Global instance
_advanced_discovery: Optional[AdvancedDiscovery] = None


def get_advanced_discovery() -> AdvancedDiscovery:
    """Get or create global advanced discovery."""
    global _advanced_discovery
    if _advanced_discovery is None:
        _advanced_discovery = AdvancedDiscovery()
    return _advanced_discovery

