"""Tests für src/llm.py: Konfiguration und Aufbau der Anfrage, ohne Endpunkt.

litellm.completion wird durch eine Attrappe ersetzt. So laufen die Tests
offline und außerhalb des Montagsfensters.
"""

from types import SimpleNamespace

import pytest

from src import llm

ENV_VARS = [
    "LLM_BASE_URL", "OPENAI_BASE_URL", "LLM_API_KEY", "OPENAI_API_KEY",
    "LLM_MODEL", "OPENAI_MODEL", "LLM_THINKING", "LLM_TIMEOUT",
]


@pytest.fixture(autouse=True)
def saubere_umgebung(monkeypatch):
    """Eure exportierten Variablen sollen die Tests nicht beeinflussen."""
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def aufrufe(monkeypatch):
    """Ersetzt litellm.completion und merkt sich die Argumente jedes Aufrufs."""
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        message = SimpleNamespace(content="OK")
        usage = SimpleNamespace(prompt_tokens=42, completion_tokens=3)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)
    return calls


def test_provider_praefix_wird_ergaenzt():
    assert llm._provider_model("qwen3.6-35B-A3B-FP8") == "hosted_vllm/qwen3.6-35B-A3B-FP8"


def test_praefixierter_name_bleibt_unveraendert():
    assert llm._provider_model("ollama/qwen2.5-coder:1.5b") == "ollama/qwen2.5-coder:1.5b"


def test_defaults_ohne_umgebungsvariablen():
    assert llm.get_base_url() == "https://llm.homecloud.ee/v1"
    assert llm.get_model() == "qwen3.6-35B-A3B-FP8"
    assert llm.get_api_key() == ""


def test_llm_variablen_haben_vorrang_vor_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "modell-b")
    monkeypatch.setenv("LLM_MODEL", "modell-a")
    assert llm.get_model() == "modell-a"


def test_chat_schickt_system_und_user_nachricht(aufrufe, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    assert llm.chat("Sag nur: OK") == "OK"

    kwargs = aufrufe[0]
    assert kwargs["model"] == "hosted_vllm/qwen3.6-35B-A3B-FP8"
    assert [m["role"] for m in kwargs["messages"]] == ["system", "user"]
    assert kwargs["messages"][0]["content"] == llm.SYSTEM_PROMPT
    assert kwargs["messages"][1]["content"] == "Sag nur: OK"
    assert kwargs["temperature"] == 0.0
    assert kwargs["api_base"] == "https://llm.homecloud.ee/v1"
    assert kwargs["api_key"] == "test-key"


def test_chat_with_usage_liefert_text_und_tokens(aufrufe):
    text, usage = llm.chat_with_usage("Sag nur: OK")
    assert text == "OK"
    assert usage == {"prompt_tokens": 42, "completion_tokens": 3}
    assert len(aufrufe) == 1


def test_chat_liefert_leeren_text_statt_none(monkeypatch):
    def fake_completion(**_kwargs):
        message = SimpleNamespace(content=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)
    assert llm.chat_with_usage("x") == ("", {"prompt_tokens": 0, "completion_tokens": 0})


def test_timeout_hat_default_und_ist_einstellbar(aufrufe, monkeypatch):
    llm.chat("x")
    monkeypatch.setenv("LLM_TIMEOUT", "5")
    llm.chat("x")
    assert aufrufe[0]["timeout"] == llm.DEFAULT_TIMEOUT_S
    assert aufrufe[1]["timeout"] == 5.0


def test_max_tokens_nur_wenn_angegeben(aufrufe):
    llm.chat("x")
    llm.chat("x", max_tokens=64)
    assert "max_tokens" not in aufrufe[0]
    assert aufrufe[1]["max_tokens"] == 64


def test_ohne_llm_thinking_bleibt_der_server_default(aufrufe):
    llm.chat("x")
    assert "extra_body" not in aufrufe[0]


@pytest.mark.parametrize("wert, erwartet", [("off", False), ("AUS", False), ("on", True)])
def test_llm_thinking_schaltet_das_chat_template(aufrufe, monkeypatch, wert, erwartet):
    monkeypatch.setenv("LLM_THINKING", wert)
    llm.chat("x")
    assert aufrufe[0]["extra_body"] == {"chat_template_kwargs": {"enable_thinking": erwartet}}


def test_konfiguration_verraet_den_key_nicht(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-geheim-123")
    monkeypatch.setenv("LLM_THINKING", "off")
    text = llm.describe_config()
    assert "sk-geheim-123" not in text
    assert "API-Key:  gesetzt" in text
    assert "Thinking: aus" in text


def test_fehlender_key_wird_gemeldet():
    assert "API-Key:  FEHLT" in llm.describe_config()
