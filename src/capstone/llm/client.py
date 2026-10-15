"""LLM client adapters."""

from __future__ import annotations

import json
from typing import Any, Protocol

from capstone.settings import LLMSettings, load_llm_settings


class LLMClient(Protocol):
    """Provider contract for schema-guided JSON generation."""

    provider: str
    model: str

    def structured_generate(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]: ...


class GroqLLMClient:
    """Groq chat-completions adapter for JSON-object structured responses."""

    provider = "groq"

    def __init__(self, settings: LLMSettings | None = None) -> None:
        config = settings or load_llm_settings()
        if config.provider != "groq":
            raise ValueError(
                "GroqLLMClient requires LLM_PROVIDER=groq in the environment or .env."
            )
        if config.groq_api_key is None:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to the project-root .env file "
                "or your environment."
            )

        try:
            from groq import Groq
        except ImportError as exc:
            raise ImportError(
                "Groq support is optional. Install it with `pip install -e '.[groq]'`."
            ) from exc

        self.model = config.groq_model
        self._client = Groq(api_key=config.groq_api_key)

    def structured_generate(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        schema_instruction = (
            "Return a valid JSON object matching this schema:\n"
            + json.dumps(schema, ensure_ascii=False)
        )
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n{schema_instruction}",
                },
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=900,
        )
        if not response.choices:
            raise ValueError("Groq returned no completion choices.")

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Groq returned an empty response.")
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("Groq response must be a JSON object.")
        return result


def create_llm_client(settings: LLMSettings | None = None) -> LLMClient:
    """Create the configured provider client; offline mock parsing stays in M1."""
    config = settings or load_llm_settings()
    if config.provider == "groq":
        return GroqLLMClient(config)
    raise NotImplementedError(
        "The package-level mock parser is not implemented. Use the deterministic "
        "mock client in the CareFlow M1 notebook or set LLM_PROVIDER=groq."
    )
