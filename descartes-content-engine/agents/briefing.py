"""
Agent 5: Briefing
Runs Friday 15:00. Generates weekly intelligence briefing stored in SQLite.
Visible in Stuart's view in the frontend.
"""
import json
import logging
from datetime import datetime, timedelta
from core import database as db
from core.llm import complete, MODEL_MAIN

logger = logging.getLogger(__name__)

BRIEFING_SYSTEM = """You are a strategic intelligence analyst for Stuart Corrigan, Descartes Consulting.
Write in Stuart's voice: direct, British English, no jargon, data-driven, systems-thinking lens.
This is a weekly briefing for Stuart — professional shorthand is fine, no need to explain who he is."""


def run(dry_run: bool = False):
    run_id = db.log_agent_run("briefing")
    logger.info("=== Briefing Agent starting ===")

    articles = db.get_week_articles(min_score=6.0)
    pain_points = db.get_pain_points()
    pending_drafts = db.get_pending_drafts()

    week_start = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")

    if not articles:
        logger.warning("No articles this week for briefing")
        db.finish_agent_run(run_id, "success", 0)
        return None

    prompt = f"""Generate a weekly intelligence briefing for Stuart Corrigan based on this week's signals.

THIS WEEK'S ARTICLES ({len(articles)} total):
{_format_articles(articles[:20])}

PENDING DRAFTS AWAITING REVIEW: {len(pending_drafts)}

Generate briefing as JSON:
{{
  "top_stories": [
    {{
      "headline": "<what happened>",
      "why_it_matters": "<system design implication for claims/pension ops>",
      "content_opportunity": "<post angle if not yet drafted>"
    }}
  ],
  "trend_watch": [
    {{
      "trend": "<emerging pattern>",
      "direction": "<accelerating|stabilising|reversing>",
      "implication": "<what Stuart should know>"
    }}
  ],
  "next_week_priorities": [
    "<specific action or watch point>"
  ],
  "opportunity_spotted": "<single biggest content or business development opportunity this week>"
}}

top_stories: exactly 3 (most important)
trend_watch: exactly 3
next_week_priorities: 3-5 items
Be specific. Use numbers where available. British English.
"""

    try:
        response = complete(prompt, system=BRIEFING_SYSTEM, max_tokens=1500, temperature=0.5)
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]

        briefing = json.loads(response.strip())
        briefing["week_start"] = week_start

        if not dry_run:
            briefing_id = db.insert_briefing(briefing)
            logger.info(f"Stored briefing #{briefing_id}")

        logger.info("=== Briefing done ===")
        db.finish_agent_run(run_id, "success", len(articles))
        return briefing

    except Exception as e:
        logger.error(f"Briefing failed: {e}")
        db.finish_agent_run(run_id, "error", 0, str(e))
        return None


def _format_articles(articles: list) -> str:
    lines = []
    for a in articles[:20]:
        lines.append(f"• {a['title']} | Score: {a.get('relevance_score', 0)} | {a.get('urgency', '')}")
        if a.get("content_angle"):
            lines.append(f"  → {a['content_angle']}")
    return "\n".join(lines)
