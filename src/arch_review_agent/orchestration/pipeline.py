"""
Pipeline stages and context for the architectural review agent.

Stages: input policy -> parse doc -> tool calling -> LLM -> output policy -> failure analysis.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from arch_review_agent.config import Settings


@dataclass
class PipelineContext:
    """Mutable context passed through the pipeline."""

    settings: Settings
    doc_path: Path
    raw_content: str = ""
    parsed_content: Any = None  # TODO: Typed parsed structure
    input_policy_ok: bool = False
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    llm_messages: list[dict[str, str]] = field(default_factory=list)
    llm_response: str = ""
    output_policy_ok: bool = False
    failure_analysis: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Final result of the pipeline."""

    success: bool
    feedback: str  # LLM-generated feedback (or aggregated)
    context: PipelineContext
    error: str | None = None


# TODO: Implement individual stage functions and wire in orchestrator:
# - run_input_policy(ctx) -> bool
# - run_parse(ctx) -> None
# - run_tools(ctx) -> None
# - run_llm(ctx) -> None
# - run_output_policy(ctx) -> bool
# - run_failure_analysis(ctx) -> None
