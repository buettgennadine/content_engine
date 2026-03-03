"""
Anthropic / Claude API wrapper for Descartes Content Engine.
All LLM calls go through here.
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv
import anthropic

load_dotenv(override=True)
logger = logging.getLogger(__name__)

MODEL_MAIN = "claude-sonnet-4-5"
MODEL_FAST = "claude-haiku-4-5-20251001"

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in .env")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def complete(
    prompt: str,
    system: str = "",
    model: str = MODEL_MAIN,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> str:
    """Single completion call. Returns text content."""
    client = get_client()
    try:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
        return response.content[0].text
    except anthropic.RateLimitError:
        logger.warning("Rate limit hit, retrying after 60s...")
        import time
        time.sleep(60)
        response = client.messages.create(**kwargs)
        return response.content[0].text
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def chat(
    system: str,
    user: str,
    model: str = MODEL_MAIN,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> str:
    """Chat-style completion with system + user messages. Returns text."""
    return complete(user, system=system, model=model, max_tokens=max_tokens, temperature=temperature)


def classify_article(title: str, snippet: str, categories: list[str]) -> dict:
    """
    Fast classification using Haiku.
    Returns: {relevance_score, categories, urgency, content_angle, data_points, content_utility}
    """
    prompt = f"""Classify this article for Stuart Corrigan's content pipeline (insurance/pension ops).

Title: {title}
Snippet: {snippet[:300]}

Relevant categories: {', '.join(categories)}

Return JSON only:
{{
  "relevance_score": <0-10, where 10=highly relevant to Claims/Pension Ops directors>,
  "categories": [<list of matching categories from the provided list>],
  "urgency": "<breaking|timely|evergreen>",
  "content_angle": "<one sentence: how could Stuart use this for a contrarian/systems-thinking LinkedIn post?>",
  "data_points": [<any specific numbers/percentages/monetary values found>],
  "content_utility": "<A|B|C|D>"
}}

content_utility:
A = Contains a specific number, statistic, data point, or measurable outcome
B = Describes a system pattern, process failure, or operational design issue
C = Transfer story — a failure/success from another industry applicable to insurance/pensions ops
D = None of the above — general news, opinion without data or pattern

Score >= 6 means relevant. Score < 6 = discard.
Focus: Claims management pain points, pension operations, regulatory pressure, systems thinking opportunities.
"""
    try:
        text = complete(prompt, model=MODEL_FAST, max_tokens=600, temperature=0.2)
        import json
        # Strip markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return {
            "relevance_score": 0,
            "categories": [],
            "urgency": "evergreen",
            "content_angle": "",
            "data_points": [],
            "content_utility": "D",
        }
