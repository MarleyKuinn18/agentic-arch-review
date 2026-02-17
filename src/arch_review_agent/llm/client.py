"""
LLM client: calls an OpenAI-compatible API for generating review feedback.

Uses httpx (no proprietary SDK). Works with Ollama, LiteLLM, vLLM, etc.
"""

from arch_review_agent.config import Settings


class LLMClient:
    """
    HTTP client for chat completions (OpenAI-compatible endpoint).
    """

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    async def chat(self, messages: list[dict[str, str]]) -> str:
        """
        Send messages and return the assistant reply content.

        TODO: Implement with httpx:
        - POST {base_url}/chat/completions
        - Body: { "model": self.model, "messages": messages }
        - Headers: Authorization if api_key set
        - Return response.choices[0].message.content or raise
        """
        # placeholder
        return ""

    async def get_feedback(self, doc_content: str, tool_summary: str = "") -> str:
        """
        Build a prompt for architecture review feedback and return LLM response.

        TODO: Build messages (system + user with doc_content and optional tool_summary),
        then call self.chat(messages).
        """
        messages = [
            {"role": "system", "content": "You are an expert software architect. Provide concise, actionable review feedback."},
            {"role": "user", "content": doc_content or "(no content)"},
        ]
        return await self.chat(messages)


async def get_feedback(settings: Settings, doc_content: str, tool_summary: str = "") -> str:
    """Convenience: create client and get feedback."""
    client = LLMClient(settings)
    return await client.get_feedback(doc_content, tool_summary)
