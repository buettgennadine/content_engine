"""
Agent 3: Ideate
Runs Sunday 20:00. Reads week's top articles (VPS > 60), generates 12 content ideas,
stores them in content_ideas table with priority scores.
"""
import json
import logging
from core import database as db
from core.llm import complete, MODEL_MAIN

logger = logging.getLogger(__name__)

STUART_VOICE_SYSTEM = """You are writing content strategy for Stuart Corrigan, Descartes Consulting Ltd.

Stuart's profile: 29+ years experience, Systems Thinking & Theory of Constraints consultant,
specialising in Insurance Claims Management and Pension Operations (UK + DACH markets).

Stuart's voice:
- British English (organisation, analyse, colour, programme)
- Short declarative sentences. Lead with the conclusion.
- Contrarian, dry humour, straight-talking practitioner
- NEVER blame individuals — always system design
- NEVER use: "transformation journey", "stakeholder buy-in", "leverage", "synergies", 
  "digital transformation", "roadmap", "change management", "best practice"

Signature phrases (use where natural):
- "This is not a people problem. It is a design problem."
- "Until the rules change, the outcomes won't."
- "Stop starting. Start finishing."

Target audience: Claims Directors, COOs, Pension Operations Directors, CFOs — UK and Germany
"""


def run(dry_run: bool = False):
    run_id = db.log_agent_run("ideate")
    logger.info("=== Ideate Agent starting ===")

    articles = db.get_week_articles(min_score=7.0)
    logger.info(f"Working with {len(articles)} articles from this week")

    if not articles:
        logger.warning("No articles above threshold — skipping ideation")
        db.finish_agent_run(run_id, "success", 0)
        return []

    pain_points = db.get_pain_points()
    pain_context = _format_pain_context(pain_points)
    articles_context = _format_articles(articles[:15])  # top 15

    prompt = f"""Based on this week's insurance industry signals, generate 12 LinkedIn content ideas for Stuart Corrigan.

THIS WEEK'S TOP SIGNALS:
{articles_context}

PAIN POINT DATABASE (use as supporting data):
{pain_context}

POST TEMPLATES AVAILABLE:
1. Old vs New Rules — Stuart's signature format. Contrasting 🔴/🟢 pairs
2. Contrarian Take — Challenges conventional wisdom with specific named belief
3. Data Hook — Opens with shocking statistic. "£11.7B. Let that sink in."
4. Case Study — Leads with dramatic result number. Anonymous. Strong trust builder.
5. Provocative Question — Opens with challenge that forces reflection
6. Story Format — Anecdote → tension → insight. High dwell time.

CONTENT PILLARS:
- Claims Management (performance, failure demand, leakage, AI/automation)
- Pension Operations (complexity, dashboards, admin burden)
- System Design vs Individual Performance
- Theory of Constraints applied to insurance
- Consumer Duty as Systems Thinking

Generate exactly 12 ideas as a JSON array:
[
  {{
    "title": "<compelling working title>",
    "format": "<template name from list above>",
    "pillar": "<content pillar>",
    "hook": "<opening line — 10-15 words, Tier 1 opening pattern>",
    "angle": "<the contrarian or systems-thinking insight>",
    "key_data": "<specific number/statistic to anchor the post>",
    "source_article_ids": [<list of article ids from the signals>],
    "priority_score": <0-100, based on VPS and timeliness>,
    "urgency": "<this_week|next_week|evergreen>",
    "effort": "<low|medium|high>"
  }}
]

Rank by priority_score descending. Top 3 will be drafted on Monday.
Ensure variety: no more than 3 ideas per template type.
"""

    try:
        response = complete(prompt, system=STUART_VOICE_SYSTEM, max_tokens=3000, temperature=0.8)
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]

        ideas = json.loads(response.strip())
        logger.info(f"Generated {len(ideas)} content ideas")

        if not dry_run:
            stored = 0
            for idea in ideas:
                db.insert_idea(idea)
                stored += 1
            logger.info(f"Stored {stored} ideas in DB")

        db.finish_agent_run(run_id, "success", len(ideas))
        return ideas

    except Exception as e:
        logger.error(f"Ideation failed: {e}")
        db.finish_agent_run(run_id, "error", 0, str(e))
        return []


def _format_articles(articles: list) -> str:
    lines = []
    for a in articles:
        vps = a.get("vps", a.get("relevance_score", 0))
        lines.append(
            f"[ID:{a['id']}] Score:{vps} | {a['title']}\n"
            f"  Angle: {a.get('content_angle', 'N/A')}\n"
            f"  Data: {a.get('data_points', '[]')}"
        )
    return "\n\n".join(lines)


def _format_pain_context(pain_points: list) -> str:
    if not pain_points:
        return "No pain point data available."
    by_cat = {}
    for pp in pain_points:
        cat = pp.get("category", "other")
        by_cat.setdefault(cat, []).append(f"{pp['data_point']}: {pp['value']}")
    lines = []
    for cat, points in by_cat.items():
        lines.append(f"{cat.upper()}: " + " | ".join(points[:3]))
    return "\n".join(lines)
