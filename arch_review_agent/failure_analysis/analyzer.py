"""
Failure mode analysis: classify and record failures for observability and improvement.

Runs after the main pipeline; can analyze ctx.errors, tool failures, policy rejections, etc.
"""

from arch_review_agent.orchestration.pipeline import PipelineContext


def run_failure_analysis(ctx: PipelineContext) -> dict[str, object]:
    """
    Analyze failure modes from the pipeline context.

    TODO: Implement:
    - Categorize errors (input policy, parse, tool, LLM, output policy)
    - Count and tag failure types
    - Optionally suggest mitigations or log for later review
    - Return a summary dict attached to ctx.failure_analysis
    """
    result: dict[str, object] = {
        "has_errors": len(ctx.errors) > 0,
        "error_count": len(ctx.errors),
        "input_policy_passed": ctx.input_policy_ok,
        "output_policy_passed": ctx.output_policy_ok,
        "tool_failures": sum(1 for t in ctx.tool_results if not t.get("success", True)),
    }
    ctx.failure_analysis = result
    return result
