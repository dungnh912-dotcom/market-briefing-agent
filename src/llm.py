from __future__ import annotations

import logging

from config import Settings

logger = logging.getLogger(__name__)


def generate_with_llm(prompt: str, settings: Settings) -> str | None:
    if settings.openai_api_key:
        return _chat_completion(
            api_key=settings.openai_api_key,
            base_url=None,
            model=settings.openai_model,
            prompt=prompt,
        )
    if settings.github_token:
        return _chat_completion(
            api_key=settings.github_token,
            base_url="https://models.github.ai/inference",
            model=settings.github_model,
            prompt=prompt,
        )
    logger.info("No LLM key found; using deterministic report writer.")
    return None


def _chat_completion(api_key: str, base_url: str | None, model: str, prompt: str) -> str | None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Bạn viết bản tin thị trường bằng tiếng Việt, thận trọng và có điều kiện."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.warning("LLM generation failed, fallback to deterministic writer: %s", exc)
        return None
