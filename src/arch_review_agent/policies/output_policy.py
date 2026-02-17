"""
Output-layer policy evaluation.

Runs after LLM response: validates that the feedback/output
is safe and compliant before returning to the user.
"""

from arch_review_agent.orchestration.pipeline import PipelineContext


def evaluate_output_policy(ctx: PipelineContext) -> bool:
    """
    Evaluate output policy. Return True if the response is allowed to be returned.

    TODO: Implement checks, e.g.:
    - No sensitive data leakage
    - Max response length
    - Content filters (e.g. no harmful advice)
    - Format compliance
    """
    # ctx.llm_response, ctx.parsed_content, ctx.tool_results available
    return True
