"""
llm.py — the single place Sprint Copilot talks to a language model.

Uses Azure OpenAI. Unlike plain OpenAI, Azure needs an endpoint, an api
version, and — importantly — you pass your *deployment name* where you'd
normally pass a model name. All of that comes from .env:

    AZURE_OPENAI_ENDPOINT      https://<your-resource>.openai.azure.com
    AZURE_OPENAI_API_KEY       the key from the Azure resource
    AZURE_OPENAI_DEPLOYMENT    the deployment you created (e.g. "gpt-4o-mini")
    AZURE_OPENAI_API_VERSION   e.g. 2024-10-21

Everything else in Sprint Copilot calls llm(system, user) and doesn't care
which provider is behind it — so swapping providers later touches only this
file.
"""

import os


def _client():
    from openai import AzureOpenAI
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


def llm(system: str, user: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
    """Send one system+user prompt, return the model's text reply."""
    client = _client()
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],  # Azure: deployment name, not model id
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()


if __name__ == "__main__":
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    print(llm("You are a test.", "Reply with exactly: ok"))
