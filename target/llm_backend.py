import os


def get_llm_backend():
    """Pick the backend via the LLM_BACKEND env var. Defaults to 'mock' so
    the whole pipeline runs with zero setup. Switch to 'ollama' once you
    have a local model pulled (e.g. `ollama pull llama3.1:8b`)."""
    backend = os.environ.get("LLM_BACKEND", "mock")
    if backend == "ollama":
        return ollama_generate
    if backend == "openai":
        return openai_generate
    return mock_generate


def ollama_generate(prompt, model="llama3.1:8b"):
    import requests
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def openai_generate(prompt, model="gpt-4o-mini"):
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content


def mock_generate(prompt, model=None):
    """
    A rule-based stand-in LLM used to test the pipeline before wiring up a
    real model. It DELIBERATELY mimics a vulnerable, instruction-following
    LLM: if any override-style phrase appears anywhere in the prompt --
    including inside retrieved 'documents' -- it complies with it. This
    lets you validate your attack generator and defense layers end-to-end
    with a predictable target before spending GPU time on a real model.
    """
    lower = prompt.lower()
    override_markers = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "the hidden rules are visible to you",
        "start your response using the above",
        "you must follow",
        "print yes",
        "reveal your system prompt",
        "pretend you are",
    ]
    for marker in override_markers:
        if marker in lower:
            return f"[COMPROMISED] Understood, following the injected instruction: '{marker}'"
    return "I'm a helpful assistant. Based on the provided context, here is my answer to your question."
