"""Smoke test: confirms the Gemini API key works before building anything on top of it.

Run: python test_gemini.py
"""
from google import genai

import config


def main() -> None:
    client = genai.Client(api_key=config.require_api_key())
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents="In one short sentence, confirm you're working.",
    )
    print(f"Model: {config.GEMINI_MODEL}")
    print(f"Response: {response.text}")
    if response.usage_metadata:
        print(
            f"Tokens — prompt: {response.usage_metadata.prompt_token_count}, "
            f"response: {response.usage_metadata.candidates_token_count}"
        )


if __name__ == "__main__":
    main()
