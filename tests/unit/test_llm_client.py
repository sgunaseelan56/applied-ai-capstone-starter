import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from capstone.llm.client import GroqLLMClient, create_llm_client
from capstone.settings import LLMSettings


def groq_settings(
    *, provider: str = "groq", api_key: str | None = "test-key", model: str = "test-model"
) -> LLMSettings:
    return LLMSettings(
        provider=provider,
        groq_api_key=api_key,
        groq_model=model,
    )


def test_groq_client_requires_groq_provider() -> None:
    with pytest.raises(ValueError, match="LLM_PROVIDER=groq"):
        GroqLLMClient(groq_settings(provider="mock"))


def test_groq_client_requires_api_key() -> None:
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        GroqLLMClient(groq_settings(api_key=None))


def test_structured_generate_sends_json_request_and_parses_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict] = []
    payload = {"urgency": "Routine"}

    class FakeGroq:
        def __init__(self, *, api_key: str) -> None:
            assert api_key == "test-key"
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self.create_completion)
            )

        def create_completion(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(payload))
                    )
                ]
            )

    monkeypatch.setitem(sys.modules, "groq", ModuleType("groq"))
    monkeypatch.setattr(sys.modules["groq"], "Groq", FakeGroq, raising=False)

    client = GroqLLMClient(groq_settings())
    result = client.structured_generate(
        system_prompt="system",
        user_prompt="user",
        schema={"type": "object"},
    )

    assert client.provider == "groq"
    assert client.model == "test-model"
    assert result == payload
    assert calls[0]["model"] == "test-model"
    assert calls[0]["response_format"] == {"type": "json_object"}
    assert calls[0]["temperature"] == 0
    assert calls[0]["max_tokens"] == 900


def test_structured_generate_rejects_non_object_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeGroq:
        def __init__(self, *, api_key: str) -> None:
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(content='["not", "an", "object"]')
                            )
                        ]
                    )
                )
            )

    monkeypatch.setitem(sys.modules, "groq", ModuleType("groq"))
    monkeypatch.setattr(sys.modules["groq"], "Groq", FakeGroq, raising=False)

    client = GroqLLMClient(groq_settings())
    with pytest.raises(ValueError, match="JSON object"):
        client.structured_generate(
            system_prompt="system",
            user_prompt="user",
            schema={"type": "object"},
        )


def test_factory_requires_groq_for_shared_package() -> None:
    with pytest.raises(NotImplementedError, match="mock parser"):
        create_llm_client(groq_settings(provider="mock"))
