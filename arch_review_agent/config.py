"""
Configuration for the architectural review agent.

Uses pydantic-settings with env and .env file loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent settings. Override via environment or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM endpoint (OpenAI-compatible: Ollama, LiteLLM, vLLM, etc.)
    llm_base_url: str = "http://localhost:11434/v1"  # Ollama default
    llm_api_key: str = ""  # Not needed for local Ollama
    llm_model: str = "llama3.2"

    # Path to architecture document (markdown)
    arch_doc_path: str = ""

    # Policy and failure analysis toggles
    enable_input_policy: bool = True
    enable_output_policy: bool = True
    enable_failure_analysis: bool = True


# TODO: Add more settings as needed (timeouts, retries, tool config, etc.)
