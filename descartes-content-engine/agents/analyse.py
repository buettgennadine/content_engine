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
    Viral Potential Score (0-100). Source Layer v2 weights.
    pain_intensity(20) + audience_fit(15) + transfer_potential(20) +
    data_strength(15) + contrarian_angle(15) + personal_hook(10) + timeliness(5)
    """
    score = 0
    categories = _parse_categories(article.get("categories", []))

    # Pain intensity (20%) — direct pain signal from claims/pensions sector
    relevance = article.get("relevance_score", 0)
    # Supports both v1 and v2 category names
    pain_cats = {"claims_pensions", "claims_management", "pension_operations",
                 "consumer_duty", "regulatory_pressure"}
    pain_match = len(pain_cats & categories)
    pain_intensity = min(100, relevance * 8 + pain_match * 15)
    score += pain_intensity * 0.20

    # Audience fit (15%) — Claims Directors, COOs, Pension Ops
    audience_cats = {"claims_pensions", "claims_management", "pension_operations"}
    audience_match = len(audience_cats & categories)
    # Stuart combo: thought_leaders or systems_thinking + pain category = bonus
    combo_cats = {"thought_leaders", "systems_thinking", "toc_lean"}
    combo_bonus = 30 if (combo_cats & categories) and (audience_cats & categories) else 0
    audience_fit = min(100, audience_match * 35 + combo_bonus)
    score += audience_fit * 0.15

    # Transfer potential (20%) — cross-industry applicability to insurance/pensions ops
    # content_utility C = explicit transfer story
    content_utility = article.get("content_utility", "D")
    utility_base = {"A": 70, "B": 80, "C": 100, "D": 30}.get(content_utility, 30)
    xfer_cats = {"cross_industry", "viral_transfer", "research", "thought_leaders",
                 "systems_thinking", "toc_lean"}
    xfer_match = len(xfer_cats & categories)
    transfer_potential = min(100, utility_base + xfer_match * 10)
    score += transfer_potential * 0.20

    # Data strength (15%) — specific numbers, stats, measurable outcomes
    data_points = _parse_list(article.get("data_points", []))
    data_strength = min(100, len(data_points) * 25)
    if _text_has_numbers(article.get("title", ""), article.get("snippet", "")):
        data_strength = max(data_strength, 60)
    # content_utility A = confirmed data point
    if content_utility == "A":
        data_strength = max(data_strength, 70)
    score += data_strength * 0.15

    # Contrarian angle (15%) — from content_angle field
    contrarian = 60 if article.get("content_angle") else 20
    score += contrarian * 0.15

    # Personal hook (10%) — connection to Stuart's methodology (TOC, Vanguard, systems)
    hook_cats = {"thought_leaders", "systems_thinking", "toc_lean"}
    hook_match = len(hook_cats & categories)
    personal_hook = min(100, hook_match * 40 + 20)
    score += personal_hook * 0.10

    # Timeliness (5%) — evergreen preferred over breaking news
    urgency = article.get("urgency", "evergreen")
    timeliness_map = {"breaking": 70, "timely": 85, "evergreen": 100}
    score += timeliness_map.get(urgency, 100) * 0.05

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

transfer_potential (0-10): How well does this story/data translate to insurance or pensions operations?
  10 = Direct insurance/pensions case with data
  7 = Adjacent industry (healthcare, aviation, finance) with clear parallel
  4 = General business with some transferability
  1 = No meaningful transfer possible

personal_hook (0-10): Does this connect to Stuart's known methodology or experience?
  10 = Direct TOC/Vanguard/CCPM application with documented results
  7 = Systems thinking angle Stuart has written about
  4 = General ops improvement Stuart could comment on
  1 = No connection to Stuart's expertise

Provide a richer analysis in JSON:
{{
  "refined_angle": "<one sentence: the strongest contrarian angle for a LinkedIn post>",
  "hook_options": ["<hook 1: direct challenge>", "<hook 2: personal experience>", "<hook 3: data-led>"],
  "system_design_insight": "<what system condition is causing the problem described>",
  "suggested_template": "<Old vs New|Contrarian Take|Data Hook|Case Study|Provocative Question|Story Format>",
  "urgency_for_content": "<post this week|next week|evergreen>",
  "transfer_potential": <0-10>,
  "personal_hook": <0-10>
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
