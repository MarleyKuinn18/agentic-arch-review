"""Main orchestrator: runs the full pipeline in order.

Pipeline: input policy -> parse -> RAG index -> retrieve -> LLM -> output policy -> failure analysis.
"""

from pathlib import Path

from arch_review_agent.config import Settings
from arch_review_agent.llm.client import LLMClient
from arch_review_agent.orchestration.pipeline import PipelineContext, PipelineResult
from arch_review_agent.parsing.markdown_parser import parse_architecture_doc
from arch_review_agent.rag.indexer import ChunkIndexer
from arch_review_agent.rag.retriever import KeywordRetriever
from arch_review_agent.schemas.review import ReviewFeedback


class Orchestrator:
    """
    Orchestrates the architectural review agent pipeline.

    Stages:
    1. Input policy evaluation
    2. Parse architecture markdown
    3. RAG indexing (chunk document)
    4. RAG retrieval (select relevant chunks)
    5. LLM invocation for feedback
    6. Output policy evaluation
    7. Failure mode analysis
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm_client = LLMClient(settings)
        self.chunk_indexer = ChunkIndexer(max_chunk_size=1500)

    async def run(self, doc_path: str | Path | None = None) -> PipelineResult:
        """
        Run the full pipeline. Uses settings.arch_doc_path if doc_path not given.
        """
        path = Path(doc_path or self.settings.arch_doc_path)
        if not path.exists():
            return PipelineResult(
                success=False,
                feedback="",
                review=None,
                context=PipelineContext(settings=self.settings, doc_path=path),
                error=f"Document not found: {path}",
            )

        ctx = PipelineContext(settings=self.settings, doc_path=path)

        try:
            # 1. Load raw content
            ctx.raw_content = path.read_text(encoding="utf-8")
            
            # 2. Input policy (optional)
            if self.settings.enable_input_policy:
                policy_ok = await self._run_input_policy(ctx)
                if not policy_ok:
                    return PipelineResult(
                        success=False,
                        feedback="",
                        review=None,
                        context=ctx,
                        error="Input policy check failed",
                    )
            ctx.input_policy_ok = True
            
            # 3. Parse markdown
            ctx.parsed_content = parse_architecture_doc(ctx.raw_content)
            
            # 4. RAG indexing
            ctx.chunks = self.chunk_indexer.index_parsed_doc(ctx.parsed_content)
            
            # 5. RAG retrieval
            if ctx.chunks:
                retriever = KeywordRetriever(ctx.chunks)
                ctx.rag_context, ctx.retrieved_chunks = retriever.get_context_for_review(
                    max_tokens=4000
                )
            else:
                # Small doc - use all content
                ctx.rag_context = ctx.raw_content
                ctx.retrieved_chunks = []
            
            # 6. LLM review
            llm_response = await self.llm_client.review_architecture(
                context=ctx.rag_context,
                chunks=ctx.retrieved_chunks,
            )
            ctx.review_feedback = ReviewFeedback.from_llm_response(llm_response)
            ctx.llm_response = ctx.review_feedback.to_markdown()
            
            # 7. Output policy (optional)
            if self.settings.enable_output_policy:
                ctx.output_policy_ok = await self._run_output_policy(ctx)
            else:
                ctx.output_policy_ok = True
            
            # 8. Failure analysis (optional)
            if self.settings.enable_failure_analysis:
                await self._run_failure_analysis(ctx)
            
            return PipelineResult(
                success=True,
                feedback=ctx.llm_response,
                review=ctx.review_feedback,
                context=ctx,
            )
            
        except Exception as e:
            ctx.errors.append(str(e))
            return PipelineResult(
                success=False,
                feedback="",
                review=None,
                context=ctx,
                error=str(e),
            )

    async def _run_input_policy(self, ctx: PipelineContext) -> bool:
        """
        Run input policy checks.
        
        Current checks:
        - Document is not empty
        - Document is not too large (>100KB)
        - Document appears to be markdown
        """
        if not ctx.raw_content.strip():
            ctx.errors.append("Document is empty")
            return False
        
        # 100KB limit for input
        if len(ctx.raw_content) > 100_000:
            ctx.errors.append("Document exceeds 100KB limit")
            return False
        
        # Basic markdown check (has at least one heading)
        if not any(line.strip().startswith("#") for line in ctx.raw_content.splitlines()):
            ctx.errors.append("Document does not appear to be markdown (no headings found)")
            return False
        
        return True

    async def _run_output_policy(self, ctx: PipelineContext) -> bool:
        """
        Run output policy checks.
        
        Current checks:
        - LLM response is not empty
        - Response was successfully parsed
        """
        if not ctx.llm_response:
            ctx.errors.append("LLM returned empty response")
            return False
        
        if ctx.review_feedback and ctx.review_feedback.raw_response:
            # JSON parsing failed, but we have raw response
            ctx.errors.append("LLM response was not valid JSON")
            # Still allow through with raw response
        
        return True

    async def _run_failure_analysis(self, ctx: PipelineContext) -> None:
        """
        Analyze and categorize any failures in the pipeline.
        """
        ctx.failure_analysis = {
            "has_errors": len(ctx.errors) > 0,
            "error_count": len(ctx.errors),
            "errors": ctx.errors,
            "chunks_indexed": len(ctx.chunks),
            "chunks_retrieved": len(ctx.retrieved_chunks),
            "llm_response_length": len(ctx.llm_response),
            "review_parsed": ctx.review_feedback is not None and ctx.review_feedback.raw_response is None,
        }
