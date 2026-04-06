"""LLM client: calls an OpenAI-compatible API for generating review feedback.

Uses httpx (no proprietary SDK). Works with Ollama, LiteLLM, vLLM, etc.
"""

import json
from typing import Any

import httpx

from arch_review_agent.config import Settings
from arch_review_agent.rag.indexer import Chunk


ARCHITECTURE_REVIEW_SYSTEM_PROMPT = """
You are an expert software architect performing a detailed Low-Level Design (LLD) review.

Your task is to analyze the provided architecture document sections and provide structured feedback.

## Review Aspects
You MUST evaluate the design across these dimensions:
1. **API Design** - RESTful conventions, endpoint naming, HTTP methods, status codes, versioning
2. **Schema Design** - Database schema, table structures, indexes, constraints
3. **Data Model** - Entity relationships, normalization, data types, foreign keys
4. **Failure Modes** - Error handling, retries, timeouts, circuit breakers, graceful degradation
5. **Observability** - Logging, metrics, tracing, monitoring, dashboards
6. **Alerting** - Alert thresholds, SLOs/SLIs, on-call considerations, anomaly detection
7. **Security** - Encryption, TLS, vulnerability considerations, threat modeling
8. **Authentication (AuthN)** - Login flows, credential management, tokens, SSO, MFA
9. **Authorization (AuthZ)** - Permissions, RBAC/ABAC, access control policies

## Output Format
You MUST respond with valid JSON in this exact structure:
```json
{
  "summary": "Brief overall assessment (2-3 sentences)",
  "strengths": [
    {
      "aspect": "<aspect_name>",
      "point": "<what is done well>",
      "section_ref": "<section title from document>",
      "anchor": "<markdown anchor link>"
    }
  ],
  "improvements": [
    {
      "aspect": "<aspect_name>",
      "severity": "critical|major|minor",
      "issue": "<what is missing or problematic>",
      "suggestion": "<specific actionable recommendation>",
      "section_ref": "<section title from document>",
      "anchor": "<markdown anchor link>"
    }
  ],
  "questions": [
    "<clarifying question about ambiguous parts of the design>"
  ],
  "missing_sections": [
    "<important sections that should be added to the document>"
  ]
}
```

## Guidelines
- Be specific and actionable in your feedback
- Reference the exact section where each issue/strength is found using the anchor link
- Prioritize critical issues (security, data integrity, failure handling) over minor style issues
- If a review aspect is not covered in the document, note it in missing_sections
- Keep suggestions practical and implementable
"""


class LLMClient:
    """
    HTTP client for chat completions (OpenAI-compatible endpoint).
    """

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send messages and return the assistant reply content.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
            
        Returns:
            Assistant message content string
            
        Raises:
            httpx.HTTPStatusError: On API errors
            ValueError: On malformed response
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract content from OpenAI-compatible response
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("No choices in LLM response")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                raise ValueError("Empty content in LLM response")
            
            return content

    async def review_architecture(
        self,
        context: str,
        chunks: list[Chunk],
    ) -> dict[str, Any]:
        """
        Perform architecture review on provided context.
        
        Args:
            context: Formatted context string from RAG retriever
            chunks: List of chunks included in context (for reference)
            
        Returns:
            Parsed JSON response with review feedback
        """
        # Build section reference info for the prompt
        section_refs = "\n".join(
            f"- [{c.section_title}](#{c.anchor}) (lines {c.start_line}-{c.end_line})"
            for c in chunks
        )
        
        user_content = f"""## Document Sections for Review

The following sections are from the architecture document. Use the anchor links when referencing specific sections.

### Available Section References:
{section_refs}

### Document Content:

{context}

---

Please review this architecture document and provide your feedback in the specified JSON format."""
        
        messages = [
            {"role": "system", "content": ARCHITECTURE_REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        
        response_text = await self.chat(messages)
        
        # Parse JSON from response (handle markdown code blocks)
        return self._parse_json_response(response_text)
    
    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.
        """
        # Try to extract JSON from markdown code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return raw text wrapped in error structure
            return {
                "summary": "Failed to parse structured response",
                "raw_response": text,
                "strengths": [],
                "improvements": [],
                "questions": [],
                "missing_sections": [],
            }

    async def get_feedback(self, doc_content: str, tool_summary: str = "") -> str:
        """
        Build a prompt for architecture review feedback and return LLM response.
        
        Legacy method for simple text feedback.
        """
        messages = [
            {"role": "system", "content": ARCHITECTURE_REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": doc_content or "(no content)"},
        ]
        return await self.chat(messages)


async def get_feedback(settings: Settings, doc_content: str, tool_summary: str = "") -> str:
    """Convenience: create client and get feedback."""
    client = LLMClient(settings)
    return await client.get_feedback(doc_content, tool_summary)
