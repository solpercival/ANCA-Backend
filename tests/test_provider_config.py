from rag_engine.config import Settings


def test_provider_defaults_are_switchable():
    settings = Settings()

    assert settings.dense_embedding_provider in {"ollama", "openai", "anthropic"}
    assert settings.sparse_embedding_provider in {"huggingface_tei"}
    assert settings.llm_provider in {"ollama", "openai", "anthropic"}
    assert settings.openai_api_key == ""
    assert settings.anthropic_api_key == ""
