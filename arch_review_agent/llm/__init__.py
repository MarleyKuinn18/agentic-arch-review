"""
LLM client for feedback generation.

Uses OpenAI-compatible API (Ollama, LiteLLM, vLLM, etc.) via HTTP.
"""

from arch_review_agent.llm.client import LLMClient, get_feedback

__all__ = ["LLMClient", "get_feedback"]
