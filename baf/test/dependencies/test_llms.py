"""Smoke tests for every dependency in requirements-llms.txt."""

import pytest


def test_openai():
    openai = pytest.importorskip("openai")
    client = openai.OpenAI(api_key="sk-test-not-a-real-key")
    assert client.api_key == "sk-test-not-a-real-key"


def test_replicate():
    replicate = pytest.importorskip("replicate")
    client = replicate.Client(api_token="r8_not_real")
    assert client


def test_transformers_import():
    transformers = pytest.importorskip("transformers")
    assert transformers.__version__
    from transformers import AutoTokenizer, pipeline  # noqa: F401


def test_anthropic():
    anthropic = pytest.importorskip("anthropic")
    client = anthropic.Anthropic(api_key="sk-ant-test-not-a-real-key")
    assert client.api_key == "sk-ant-test-not-a-real-key"
