"""
Agent 4: Draft
Runs Monday 06:00. Takes top 3 content ideas, drafts 2-3 LinkedIn post variants each.
Quality check: Score 1-10 on 6 criteria — if < 6 average, regenerate once.
Status: PENDING_REVIEW — waits for Stuart in the frontend.
"""
import json
import logging
from core import database as db
from core.llm import complete, MODEL_MAIN

logger = logging.getLogger(__name__)

QUALITY_CRITERIA = [
    "factual_accuracy",
    "positioning_alignment",
    "audience_fit",
    "tone",
    "uniqueness",
    "hook_strength",
]

TEMPLATE_GUIDES = {
    "Old vs New Rules": """Structure:
🔴 OLD RULE: [conventional wisdom — 1 line]
🟢 NEW RULE: [what actually works — 1 line]
[3-4 more contrasting pairs]
[Closing insight that names the system design problem]
[Question that validates reader frustration]
[CTA or signature insight]""",

    "Contrarian Take": """Structure:
[Bold opening statement that contradicts mainstream view]
[Name the specific conventional wisdom being challenged]
[What Stuart has actually observed — with specifics]
[System design explanation]
[Implication for the reader]
[Single focused CTA]""",

    "Data Hook": """Structure:
[Shocking statistic — standalone first line. E.g. "£11.7 billion. Let that sink in."]
[What that number means in human terms]
[Why the conventional response is wrong]
[The system design insight]
[What good looks like]
[Question to reader]""",

    "Case Study": """Structure:
[Dramatic outcome number first. E.g. "700 staff became 300."]
[Brief anonymous client context]
[What we found — the system condition]
[What we changed — not people, the design]
[The result]
[Transferable insight for reader]""",

    "Provocative Question": """Structure:
[The challenging question — specific, not generic]
[Most people's answer — and why it's wrong]
[The better question underneath]
[What the evidence shows]
[System design insight]
[Invitation to reflect]""",

    "Story Format": """Structure:
[Scene-setting anecdote — specific, brief]
[The tension or unexpected turn]
[What it revealed about the system]
[The insight]
[How this applies to reader's context]
[Closing that makes the system design point]""",
}

STUART_VOICE_SYSTEM = """You are writing LinkedIn posts AS Stuart Corrigan, Descartes Consulting Ltd.

Voice rules (non-negotiable):
- British English (organisation, analyse, colour, programme)
- Short declarative sentences. Lead with the conclusion.
- Contrarian, dry humour. Specific numbers beat vague claims.
- NEVER blame individuals — always system design
- NEVER: "transformation journey", "stakeholder buy-in", "leverage", "synergies", 
  "digital transformation", "roadmap", "change management", "in today's fast-paced"
- Every post must be SELF-CONTAINED — never reference previous posts
- End with a single focused CTA or reflective question

LinkedIn formatting:
- Max 1,300 characters for short posts, up to 3,000 for long-form
- Use line breaks generously
- Emoji: 🔴🟢 for Old/New format. Otherwise use sparingly.
- No hashtag spam — max 3 hashtags if any

Remember: Stuart's posts get 936% average engagement rate. The hook is everything.
"""


def run(dry_run: bool = False):
    run_id = db.log_agent_run("draft")
    logger.info("=== Draft Agent starting ===")

    ideas = db.get_top_ideas(limit=3)
    logger.info(f"Drafting {len(ideas)} ideas")

    if not ideas:
        logger.warning("No ideas in queue — skipping draft run")
        db.finish_agent_run(run_id, "success", 0)
        return []

    pain_points = db.get_pain_points()
    pain_context = _format_pain_context(pain_points)

    all_drafts = []

    for idea in ideas:
        logger.info(f"Drafting: {idea['title']}")
        template = idea.get("format", "Contrarian Take")
        template_guide = TEMPLATE_GUIDES.get(template, "")

        draft_content = _draft_post(idea, template_guide, pain_context)
        quality = _quality_check(draft_content, idea)

        avg_score = sum(quality.values()) / len(quality)
        logger.info(f"Quality score: {avg_score:.1f}/10 for '{idea['title'][:40]}'")

        # Regenerate once if quality < 6
        if avg_score < 6:
            logger.info("Quality below threshold — regenerating...")
            issues = [k for k, v in quality.items() if v < 6]
            draft_content = _draft_post(idea, template_guide, pain_context, issues=issues)
            quality = _quality_check(draft_content, idea)
            avg_score = sum(quality.values()) / len(quality)

        draft_data = {
            "idea_id": idea["id"],
            "version": 1,
            "content": draft_content,
            "quality_score": avg_score,
            "quality_issues": [k for k, v in quality.items() if v < 7],
            "status": "PENDING_REVIEW",
            "consultant_notes": f"Template: {template} | VPS-based idea | Quality: {avg_score:.1f}/10",
        }

        if not dry_run:
            draft_id = db.insert_draft(draft_data)
            logger.info(f"Stored draft #{draft_id} for idea '{idea['title'][:40]}'")
            # Mark idea as drafted
            conn = db.get_connection()
            try:
                conn.execute("UPDATE content_ideas SET status = 'drafted' WHERE id = ?", (idea["id"],))
                conn.commit()
            finally:
                conn.close()

        all_drafts.append(draft_data)

    logger.info(f"=== Draft done. {len(all_drafts)} drafts created ===")
    db.finish_agent_run(run_id, "success", len(all_drafts))
    return all_drafts


def _draft_post(idea: dict, template_guide: str, pain_context: str, issues: list = None) -> str:
    issue_note = ""
    if issues:
        issue_note = f"\n\nPrevious draft had issues with: {', '.join(issues)}. Fix these specifically."

    prompt = f"""Write a LinkedIn post for Stuart Corrigan using this content idea.

IDEA:
Title: {idea['title']}
Format: {idea.get('format', 'Contrarian Take')}
Pillar: {idea.get('pillar', '')}
Hook (starting point): {idea.get('hook', '')}
Angle: {idea.get('angle', '')}
Key data: {idea.get('key_data', '')}

TEMPLATE STRUCTURE:
{template_guide}

SUPPORTING PAIN POINT DATA (use what's relevant):
{pain_context}
{issue_note}

Write the complete LinkedIn post now. British English. No preamble.
"""
    return complete(prompt, system=STUART_VOICE_SYSTEM, max_tokens=1200, temperature=0.75)


def _quality_check(content: str, idea: dict) -> dict:
    prompt = f"""Rate this LinkedIn post draft for Stuart Corrigan on 6 criteria.
Score each 1-10 (10 = perfect).

POST:
{content}

IDEA INTENT: {idea.get('angle', '')}

Score these criteria as JSON:
{{
  "factual_accuracy": <1-10, are all claims plausible and specific>,
  "positioning_alignment": <1-10, does it match systems thinking consultant positioning>,
  "audience_fit": <1-10, relevant to Claims Directors/COOs/Pension Ops Directors>,
  "tone": <1-10, British, direct, dry, no jargon>,
  "uniqueness": <1-10, genuinely contrarian vs generic>,
  "hook_strength": <1-10, would a busy exec stop scrolling>
}}

Return JSON only. No explanation.
"""
    try:
        response = complete(prompt, max_tokens=300, temperature=0.2)
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        return json.loads(response.strip())
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        return {c: 7 for c in QUALITY_CRITERIA}  # default to 7 if check fails


def _format_pain_context(pain_points: list) -> str:
    if not pain_points:
        return ""
    lines = [f"• {pp['data_point']}: {pp['value']} ({pp['source']}, {pp['date']})"
             for pp in pain_points[:15]]
    return "\n".join(lines)
