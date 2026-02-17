"""
Main orchestrator: runs the full pipeline in order.

Pipeline: input policy -> parse -> tools -> LLM -> output policy -> failure analysis.
"""

from pathlib import Path

from arch_review_agent.config import Settings
from arch_review_agent.orchestration.pipeline import PipelineContext, PipelineResult


class Orchestrator:
    """
    Orchestrates the architectural review agent pipeline.

    Stages:
    1. Input policy evaluation
    2. Parse architecture markdown
    3. Local tool calling
    4. LLM invocation for feedback
    5. Output policy evaluation
    6. Failure mode analysis
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(self, doc_path: str | Path | None = None) -> PipelineResult:
        """
        Run the full pipeline. Uses settings.arch_doc_path if doc_path not given.
        """
        path = Path(doc_path or self.settings.arch_doc_path)
        if not path.exists():
            return PipelineResult(
                success=False,
                feedback="",
                context=PipelineContext(settings=self.settings, doc_path=path),
                error=f"Document not found: {path}",
            )

        ctx = PipelineContext(settings=self.settings, doc_path=path)

        # TODO: Implement each stage and short-circuit on policy failures
        # 1. Load raw content
        # ctx.raw_content = path.read_text(encoding="utf-8")
        # 2. Input policy
        # if self.settings.enable_input_policy and not await run_input_policy(ctx): ...
        # 3. Parse markdown
        # await run_parse(ctx)
        # 4. Tool calling
        # await run_tools(ctx)
        # 5. LLM
        # await run_llm(ctx)
        # 6. Output policy
        # if self.settings.enable_output_policy and not run_output_policy(ctx): ...
        # 7. Failure analysis
        # if self.settings.enable_failure_analysis: await run_failure_analysis(ctx)

        return PipelineResult(
            success=True,
            feedback=ctx.llm_response or "(no feedback yet)",
            context=ctx,
        )
