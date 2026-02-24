"""
Agent 2: Analyse
Runs daily at 18:00. Scores articles with VPS, extracts pain points,
identifies content hooks. Only articles with VPS > 60 proceed to ideation.
"""
import json
import logging
from datetime import datetime
from core import database as db
from core.llm import complete, MODEL_MAIN

logger = logging.getLogger(__name__)

VPS_THRESHOLD = 60


def _parse_categories(raw) -> set:
    """Safely parse categories from DB (JSON string or list)."""
    if isinstance(raw, set):
        return raw
    if isinstance(raw, list):
        return set(raw)
    if isinstance(raw, str):
        try:
            return set(json.loads(raw))
        except Exception:
            return set()
    return set()


def _parse_list(raw) -> list:
    """Safely parse a JSON list field from DB."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []


def _text_has_numbers(title: str, snippet: str) -> bool:
    """Check if title or snippet contains numbers/percentages/monetary values."""
    import re
    text = f"{title} {snippet}"
    return bool(re.search(r'[\d]+[%£$€MBKm]|[\d]+\.[\d]+|[\d]{2,}', text))


def calculate_vps(article: dict) -> float:
    """
    Viral Potential Score (0-100).
    pain_intensity(25) + audience_fit(20) + timeliness(18) +
    contrarian_angle(15) + data_richness(12) + systems_thinking(7) + engagement_history(3)
    """
    score = 0
    categories = _parse_categories(article.get("categories", []))

    # Pain intensity (25%) — from relevance score and categories
    relevance = article.get("relevance_score", 0)
    pain_cats = {"claims_management", "pension_operations", "consumer_duty", "regulatory_pressure"}
    pain_match = len(pain_cats & categories)
    # AI claims automation, FCA enforcement = high pain signal
    high_pain_cats = {"claims_management", "claims_technology", "regulatory_pressure"}
    high_pain_match = len(high_pain_cats & categories)
    pain_intensity = min(100, relevance * 8 + pain_match * 15 + high_pain_match * 10)
    score += pain_intensity * 0.25

    # Audience fit (20%) — Claims Directors, COOs, Pension Ops + systems thinkers
    audience_cats = {"claims_management", "pension_operations", "claims_technology"}
    audience_match = len(audience_cats & categories)
    # claims_mgmt + systems_thinking = automatic 75+ for Stuart's audience
    stuart_combo = {"claims_management", "systems_thinking"}
    combo_bonus = 35 if stuart_combo.issubset(categories) else 0
    audience_fit = min(100, audience_match * 35 + combo_bonus)
    score += audience_fit * 0.20

    # Timeliness (18%)
    urgency = article.get("urgency", "evergreen")
    timeliness_map = {"breaking": 100, "timely": 80, "evergreen": 40}
    score += timeliness_map.get(urgency, 40) * 0.18

    # Contrarian angle (15%) — from content_angle field
    contrarian = 60 if article.get("content_angle") else 20
    score += contrarian * 0.15

    # Data richness (12%) — from data_points + title/snippet number scan
    data_points = _parse_list(article.get("data_points", []))
    data_richness = min(100, len(data_points) * 25)
    # If title/snippet contains numbers or percentages, floor at 60
    if _text_has_numbers(article.get("title", ""), article.get("snippet", "")):
        data_richness = max(data_richness, 60)
    score += data_richness * 0.12

    # Systems thinking fit (7%)
    toc_cats = {"systems_thinking", "toc_lean"}
    toc_match = len(toc_cats & categories)
    systems_fit = min(100, toc_match * 50 + 20)
    score += systems_fit * 0.07

    # Engagement history (3%) — static for now, will learn over time
    score += 50 * 0.03

    return round(score, 1)


def run(dry_run: bool = False):
    run_id = db.log_agent_run("analyse")
    logger.info("=== Analyse Agent starting ===")

    articles = db.get_recent_articles(hours=24, min_score=6.0)
    logger.info(f"Analysing {len(articles)} articles from last 24h")

    high_vps = []

    for article in articles:
        vps = calculate_vps(article)
        logger.info(f"VPS {vps:5.1f} — {article['title'][:60]}")

        # Persist VPS score to DB for every article
        if not dry_run:
            db.update_vps_score(article["id"], vps)

        if vps >= VPS_THRESHOLD:
            high_vps.append({**article, "vps": vps})

    logger.info(f"VPS scores persisted for {len(articles)} articles")

    if not high_vps:
        logger.info("No articles above VPS threshold today")
        db.finish_agent_run(run_id, "success", 0)
        return []

    # Deep analysis on high-VPS articles
    pain_points = db.get_pain_points()
    pain_context = _format_pain_points(pain_points)

    for article in high_vps:
        _deep_analyse(article, pain_context, dry_run)

    logger.info(f"=== Analyse done. {len(high_vps)} signals above VPS {VPS_THRESHOLD} ===")
    db.finish_agent_run(run_id, "success", len(high_vps))
    return high_vps


def _format_pain_points(pain_points: list) -> str:
    if not pain_points:
        return "No pain point data available."
    lines = []
    for pp in pain_points[:20]:  # top 20 to stay within context
        lines.append(f"• [{pp['category']} / {pp['country']}] {pp['data_point']}: {pp['value']} (Source: {pp['source']}, {pp['date']})")
    return "\n".join(lines)


def _deep_analyse(article: dict, pain_context: str, dry_run: bool):
    """Use Claude to generate a richer content angle for high-VPS articles."""
    prompt = f"""You are a content strategist for Stuart Corrigan, a systems thinking consultant specialising in insurance Claims Management and Pension Operations.

Article:
Title: {article['title']}
Snippet: {article.get('snippet', '')[:400]}
Current angle: {article.get('content_angle', '')}

Known pain points in the sector:
{pain_context}

Stuart's voice: Straight-talking, British English, contrarian, dry humour. 
Anti-language: never use "transformation journey", "stakeholder buy-in", "leverage", "synergies".
Core rule: Never blame individuals — always blame system design.

Provide a richer analysis in JSON:
{{
  "refined_angle": "<one sentence: the strongest contrarian angle for a LinkedIn post>",
  "hook_options": ["<hook 1: direct challenge>", "<hook 2: personal experience>", "<hook 3: data-led>"],
  "system_design_insight": "<what system condition is causing the problem described>",
  "suggested_template": "<Old vs New|Contrarian Take|Data Hook|Case Study|Provocative Question|Story Format>",
  "urgency_for_content": "<post this week|next week|evergreen>"
}}
"""
    try:
        response = complete(prompt, max_tokens=800, temperature=0.5)
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        analysis = json.loads(response.strip())

        if not dry_run:
            # Update article with enriched analysis
            conn = db.get_connection()
            try:
                conn.execute(
                    "UPDATE articles SET analysis = ?, status = 'analysed' WHERE id = ?",
                    (json.dumps(analysis), article["id"])
                )
                conn.commit()
            finally:
                conn.close()

    except Exception as e:
        logger.error(f"Deep analysis failed for article {article['id']}: {e}")
