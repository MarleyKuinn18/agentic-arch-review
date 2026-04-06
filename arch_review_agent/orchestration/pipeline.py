"""Pipeline stages and context for the architectural review agent.

Stages: input policy -> parse doc -> RAG index -> retrieve -> LLM -> output policy -> failure analysis.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from arch_review_agent.config import Settings
from arch_review_agent.rag.indexer import Chunk
from arch_review_agent.schemas.review import ReviewFeedback


@dataclass
class PipelineContext:
    """Mutable context passed through the pipeline."""

    settings: Settings
    doc_path: Path
    raw_content: str = ""
    parsed_content: dict[str, Any] | None = None
    input_policy_ok: bool = False
    
    # RAG fields
    chunks: list[Chunk] = field(default_factory=list)
    retrieved_chunks: list[Chunk] = field(default_factory=list)
    rag_context: str = ""
    
    # LLM fields
    llm_messages: list[dict[str, str]] = field(default_factory=list)
    llm_response: str = ""
    review_feedback: ReviewFeedback | None = None
    
    # Policy and analysis
    output_policy_ok: bool = False
    failure_analysis: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Final result of the pipeline."""

    success: bool
    feedback: str  # LLM-generated feedback as markdown
    review: ReviewFeedback | None  # Structured feedback
    context: PipelineContext
    error: str | None = None
