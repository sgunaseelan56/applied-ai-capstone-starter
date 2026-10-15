"""Environment-backed settings for the capstone runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"


@dataclass(frozen=True)
class LLMSettings:
    """LLM provider settings; API keys are read from the environment only."""

    provider: str
    groq_api_key: str | None
    groq_model: str


def load_llm_settings() -> LLMSettings:
    """Load `.env` from the project root, then resolve the current environment."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass
    else:
        load_dotenv(PROJECT_ROOT / ".env", override=False)

    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider not in {"mock", "groq"}:
        raise ValueError(
            f"Unsupported LLM_PROVIDER={provider!r}. Choose 'mock' or 'groq'."
        )

    api_key = os.getenv("GROQ_API_KEY")
    return LLMSettings(
        provider=provider,
        groq_api_key=api_key.strip() if api_key and api_key.strip() else None,
        groq_model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()
        or DEFAULT_GROQ_MODEL,
    )
