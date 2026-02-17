"""
Input-layer policy evaluation.

Runs before processing: validates that the incoming request/document
is allowed and meets policy (e.g. format, size, content checks).
"""

from arch_review_agent.orchestration.pipeline import PipelineContext


async def evaluate_input_policy(ctx: PipelineContext) -> bool:
    """
    Evaluate input policy. Return True if the input is allowed to proceed.

    TODO: Implement checks, e.g.:
    - Max document size
    - Allowed file type / markdown structure
    - Content allowlist/blocklist (e.g. no PII)
    - Rate or quota if applicable
    """
    # ctx.raw_content, ctx.doc_path available
    return True
