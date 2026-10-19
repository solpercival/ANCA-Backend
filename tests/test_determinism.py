"""Tests for deterministic generation (temperature 0 + fixed seed)."""

import json

import httpx

from rag_engine.config import get_settings
from rag_engine.providers import OllamaGenerator


async def test_deterministic_on_sends_temperature_and_seed():
    settings = get_settings()
    sent = []

    def fake_ollama(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, text=json.dumps({"response": "answer", "done": True}))

    async with httpx.AsyncClient(transport=httpx.MockTransport(fake_ollama)) as client:
        await OllamaGenerator(client).generate("prompt", deterministic=True)

    options = sent[0]["options"]
    assert options["temperature"] == settings.deterministic_temperature
    assert options["seed"] == settings.deterministic_seed


async def test_deterministic_off_sends_no_seed_and_the_configured_temperature():
    # off, the request keeps LLM_TEMPERATURE as before the flag existed; only the
    # fixed seed (and the deterministic temperature) depend on the flag
    settings = get_settings()
    sent = []

    def fake_ollama(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, text=json.dumps({"response": "answer", "done": True}))

    async with httpx.AsyncClient(transport=httpx.MockTransport(fake_ollama)) as client:
        await OllamaGenerator(client).generate("prompt", deterministic=False)

    options = sent[0]["options"]
    assert options["temperature"] == settings.llm_temperature
    assert "seed" not in options