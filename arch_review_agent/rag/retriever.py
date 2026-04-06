"""
Keyword-based retriever for RAG.

Uses TF-IDF-like scoring to retrieve relevant chunks based on query keywords.
"""

import re
from collections import Counter
from typing import Any

from arch_review_agent.rag.indexer import Chunk, extract_keywords


class KeywordRetriever:
    """
    Retrieves relevant chunks using keyword matching with TF-IDF-like scoring.
    
    For architecture review, we boost certain domain-specific terms.
    """
    
    # Domain-specific terms to boost in scoring
    DOMAIN_BOOST_TERMS = frozenset([
        # API design
        "api", "rest", "graphql", "grpc", "endpoint", "request", "response",
        "http", "status", "method", "get", "post", "put", "delete", "patch",
        # Schema / Data model
        "schema", "model", "entity", "table", "column", "field", "type",
        "database", "db", "sql", "nosql", "index", "key", "foreign", "primary",
        "relationship", "one-to-many", "many-to-many", "normalization",
        # Failure modes
        "failure", "error", "exception", "retry", "timeout", "fallback",
        "circuit", "breaker", "degradation", "graceful", "recovery",
        # Observability
        "observability", "logging", "log", "metrics", "metric", "tracing",
        "trace", "span", "monitoring", "dashboard", "prometheus", "grafana",
        # Alerting
        "alert", "alerting", "notification", "pager", "oncall", "sla", "slo",
        "sli", "threshold", "anomaly",
        # Security
        "security", "secure", "vulnerability", "attack", "threat", "risk",
        "encryption", "tls", "ssl", "https", "certificate",
        # AuthN / AuthZ
        "authentication", "authn", "login", "password", "credential", "token",
        "jwt", "oauth", "oidc", "saml", "sso", "mfa", "2fa",
        "authorization", "authz", "permission", "role", "rbac", "abac",
        "access", "control", "policy", "scope", "claim",
    ])
    
    DOMAIN_BOOST_FACTOR = 2.0
    
    def __init__(self, chunks: list[Chunk]):
        """
        Initialize retriever with indexed chunks.
        
        Args:
            chunks: List of Chunk objects from ChunkIndexer
        """
        self.chunks = chunks
        self._build_index()
    
    def _build_index(self) -> None:
        """Build inverted index and document frequency counts."""
        self.inverted_index: dict[str, list[int]] = {}
        self.doc_freq: Counter[str] = Counter()
        
        for idx, chunk in enumerate(self.chunks):
            for keyword in chunk.keywords:
                if keyword not in self.inverted_index:
                    self.inverted_index[keyword] = []
                self.inverted_index[keyword].append(idx)
                self.doc_freq[keyword] += 1
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.1,
    ) -> list[tuple[Chunk, float]]:
        """
        Retrieve top-k relevant chunks for a query.
        
        Args:
            query: Search query string
            top_k: Maximum number of chunks to return
            min_score: Minimum relevance score threshold
            
        Returns:
            List of (Chunk, score) tuples, sorted by relevance
        """
        query_keywords = extract_keywords(query)
        if not query_keywords:
            return []
        
        scores: dict[int, float] = {}
        
        for keyword in query_keywords:
            if keyword not in self.inverted_index:
                continue
            
            # IDF-like weight: rarer terms are more important
            idf = 1.0 / (1.0 + self.doc_freq[keyword])
            
            # Boost domain-specific terms
            boost = self.DOMAIN_BOOST_FACTOR if keyword in self.DOMAIN_BOOST_TERMS else 1.0
            
            for chunk_idx in self.inverted_index[keyword]:
                if chunk_idx not in scores:
                    scores[chunk_idx] = 0.0
                scores[chunk_idx] += idf * boost
        
        # Normalize by query size
        for idx in scores:
            scores[idx] /= len(query_keywords)
        
        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Filter by min_score and limit to top_k
        results = [
            (self.chunks[idx], score)
            for idx, score in ranked
            if score >= min_score
        ][:top_k]
        
        return results
    
    def retrieve_by_aspects(
        self,
        aspects: list[str],
        chunks_per_aspect: int = 3,
    ) -> dict[str, list[tuple[Chunk, float]]]:
        """
        Retrieve chunks relevant to specific review aspects.
        
        Args:
            aspects: List of aspect names (e.g., ["api_design", "security"])
            chunks_per_aspect: Max chunks to retrieve per aspect
            
        Returns:
            Dict mapping aspect name to list of (Chunk, score) tuples
        """
        aspect_queries = {
            "api_design": "api rest endpoint request response http method status code contract",
            "schema_design": "schema model entity table column field type database index",
            "data_model": "data model entity relationship table foreign key primary normalization",
            "failure_modes": "failure error exception retry timeout fallback circuit breaker recovery degradation",
            "observability": "observability logging metrics tracing monitoring dashboard prometheus grafana span",
            "alerting": "alert notification pager oncall sla slo threshold anomaly detection",
            "security": "security vulnerability attack threat encryption tls https certificate risk",
            "authn": "authentication login password credential token jwt oauth sso mfa",
            "authz": "authorization permission role rbac access control policy scope",
        }
        
        results: dict[str, list[tuple[Chunk, float]]] = {}
        
        for aspect in aspects:
            query = aspect_queries.get(aspect, aspect)
            results[aspect] = self.retrieve(query, top_k=chunks_per_aspect)
        
        return results
    
    def get_context_for_review(
        self,
        max_tokens: int = 4000,
        chars_per_token: int = 4,
    ) -> tuple[str, list[Chunk]]:
        """
        Build context string for LLM review, respecting token limit.
        
        Retrieves chunks across all review aspects and combines them.
        
        Args:
            max_tokens: Approximate max tokens for context
            chars_per_token: Estimated characters per token
            
        Returns:
            Tuple of (context_string, list of included chunks)
        """
        max_chars = max_tokens * chars_per_token
        
        # Get chunks for all review aspects
        aspects = [
            "api_design", "schema_design", "data_model", "failure_modes",
            "observability", "alerting", "security", "authn", "authz",
        ]
        aspect_results = self.retrieve_by_aspects(aspects, chunks_per_aspect=2)
        
        # Deduplicate chunks while preserving order
        seen_anchors: set[str] = set()
        unique_chunks: list[Chunk] = []
        
        for aspect in aspects:
            for chunk, score in aspect_results.get(aspect, []):
                if chunk.anchor not in seen_anchors:
                    seen_anchors.add(chunk.anchor)
                    unique_chunks.append(chunk)
        
        # Build context string within token limit
        context_parts: list[str] = []
        included_chunks: list[Chunk] = []
        current_chars = 0
        
        for chunk in unique_chunks:
            chunk_str = chunk.to_context_str()
            if current_chars + len(chunk_str) > max_chars:
                break
            context_parts.append(chunk_str)
            included_chunks.append(chunk)
            current_chars += len(chunk_str) + 2  # +2 for newlines
        
        context = "\n\n".join(context_parts)
        return context, included_chunks
