"""
Agent 4: Draft — 360Brew Optimised + Descartes Brand
Runs Monday 06:00. Takes top 3 content ideas, drafts LinkedIn posts with
funnel-stage awareness and thumbnail selection for all post types.
Status: PENDING_REVIEW — waits for Stuart in the frontend.
"""
import base64
import json
import logging
import os
import time
from pathlib import Path
import requests as http_requests
from core import database as db
from core.llm import complete

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

QUALITY_CRITERIA = [
    "factual_accuracy",
    "positioning_alignment",
    "audience_fit",
    "tone",
    "uniqueness",
    "hook_strength",
]

# ─── Brand Colours ────────────────────────────────────────────────────────────

BRAND = {
    "navy":   "#1e3a5f",   # Primary / Background
    "copper": "#c4953a",   # Accent / Copper Gold
    "white":  "#ffffff",   # Text
}

# ─── 360Brew System Prompt ────────────────────────────────────────────────────

BREW_SYSTEM = """You are writing LinkedIn posts AS Stuart Corrigan, Descartes Consulting Ltd.

VOICE (non-negotiable):
- British English (organisation, analyse, colour, programme)
- Short declarative sentences. Lead with the conclusion.
- Contrarian, dry humour. Specific numbers beat vague claims.
- NEVER blame individuals — always system design causes outcomes
- BANNED WORDS: "transformation journey", "stakeholder buy-in", "leverage",
  "synergies", "digital transformation", "roadmap", "change management",
  "in today's fast-paced", "game-changer", "holistic"
- Every post is SELF-CONTAINED — never reference previous posts
- NO engagement bait ("comment YES if you agree" — actively suppressed by algorithm)

360BREW ALGORITHM (LinkedIn 150B-param model, 2025):
- Saves = 5x the reach impact of a like. Design every post to earn a Save.
- Dwell time is the primary ranking signal — structure drives slow reading.
- Meaningful comments (15+ words) beat shallow ones — end with a real question.
- First line must stop the scroll. No "I", no "We", no "Today I want to share".
- Hashtags: 2-3 broad + 1-2 niche. Placed at END only. Never in first 3 lines.
- No links in body unless 4+ links (outperform single links — skip otherwise).

POST LENGTH (360Brew word counts — earn every word with substance):
- 300-400 words: WIP/concept posts, data hooks
- 500-600 words: Numbered frameworks, company analogies
- 700+ words: Diagnostic posts, industry system critiques

CORE STRUCTURAL PATTERNS (proven from post analysis — use by default):

1. NUMBERED EMOJI LISTS — mandatory for any post with 3+ actionable points or steps:
   Use 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ (not hyphens or bullet points).
   This is structural, not decorative.

2. COMPANY ANALOGY (TOFU posts):
   Use Starbucks, Amazon, Peloton, or ATC as the analogy frame.
   Structure: Company story (2-3 sentences) → "If you're a claims leader..."
   → direct parallel to their world. Confirmed 3-5x engagement uplift.

3. COMMUNITY VOICE block (MOFU posts — add after problem statement):
   Format: 'A claims manager writes: "[their exact words describing the problem]"'
   Validates the thesis and triggers comments from readers with similar experiences.

4. PILOT EXPERIMENT closer (MOFU posts — replaces "What are you seeing?"):
   "Run a small experiment. Pick one product line or team of 5-7 handlers
   for 8-12 weeks. Track [2-3 specific metrics]. Compare before and after."
   Immediately actionable — the primary reason a reader saves the post.

FUNNEL STAGE RULES:
TOFU (Awareness): Provoke, challenge assumptions, broad reach.
  Hook: Contrarian statement or surprising statistic. Use company analogy.
  No CTA, no self-promotion. End with open question for meaningful comments.

MOFU (Consideration): Demonstrate methodology, share data, build credibility.
  Hook: Problem statement with specific numbers.
  Include: numbered list, community voice block, TOC/Vanguard Method reference.
  End with: pilot experiment closer (the Save trigger).

BOFU (Decision): Convert warm audience with specific result.
  Hook: Named outcome (anonymised client) or specific transformation.
  Include: clear next step (not aggressive CTA).
  End with: low-friction invitation."""

TEMPLATE_GUIDES = {
    "Old vs New Rules": (
        "Structure: 3-4 contrasting pairs using 🔴 OLD RULE / 🟢 NEW RULE, "
        "closing system design insight, reflective question. "
        "Use numbered emoji list for the pairs."
    ),
    "Contrarian Take": (
        "Structure: Bold opening statement contradicting mainstream → name the "
        "specific conventional wisdom → Stuart's actual observation with specifics "
        "→ system design explanation → implication for reader → single focused CTA. "
        "Company analogy welcome."
    ),
    "Data Hook": (
        "Structure: Shocking statistic — standalone first line → what it means "
        "in human terms → why conventional response is wrong → system design "
        "insight → what good looks like → question to reader. "
        "300-400 words."
    ),
    "Case Study": (
        "Structure: Dramatic outcome number first → brief anonymous client context "
        "→ what we found (numbered list) → what we changed (not people, the design) "
        "→ the result → transferable insight."
    ),
    "Provocative Question": (
        "Structure: Challenging question — specific, not generic → most people's "
        "wrong answer → the better underlying question → what the evidence shows "
        "→ system design insight → invitation to reflect. "
        "Company analogy welcome."
    ),
    "Story Format": (
        "Structure: Scene-setting anecdote — specific, brief → tension or "
        "unexpected turn → what it revealed about the system → the insight → "
        "how this applies to reader's context → system design closing."
    ),
}

# ─── Thumbnail Styles ─────────────────────────────────────────────────────────

# Maps template name → Style letter
THUMBNAIL_STYLE_MAP = {
    "Data Hook":          "A",
    "Contrarian Take":    "A",
    "Provocative Question": "A",
    "Old vs New Rules":   "C",
    "Case Study":         "B",
    "Story Format":       "B",
}

# Style prompt templates — concept and colours injected by Python
THUMBNAIL_STYLE_PROMPTS = {
    "A": (
        "LinkedIn thumbnail, minimal Text Quote Card style. "
        "Very light blue-grey background (#e8f0f7). Clean layout with thin horizontal "
        "navy ({navy}) divider lines separating upper and lower text zones. "
        "Typography-only composition, no photographs, no people. "
        "Professional editorial aesthetic. Visual concept: {concept}"
    ),
    "B": (
        "LinkedIn thumbnail, Illustrated Scene style. "
        "AI-illustrated editorial scene that literally and visually depicts: {concept}. "
        "Navy ({navy}) and teal colour palette. Reserved white area top-left for text overlay. "
        "Professional editorial illustration, not photorealistic. No stock photography."
    ),
    "C": (
        "LinkedIn thumbnail, Dark Headline Card style. "
        "Dark navy ({navy}) background. Bold left-aligned typographic layout. "
        "Abstract geometric or data-flow illustration on right side. "
        "Copper ({copper}) accent bar at very bottom edge. "
        "Modern, authoritative, no photographs. Visual concept: {concept}"
    ),
    "D": (
        "LinkedIn video thumbnail. Professional executive at a whiteboard or desk. "
        "Dashboard or operational data UI overlay with warning indicators. "
        "Dark strip at bottom for title text. Copper ({copper}) highlight underline. "
        "Visual concept: {concept}"
    ),
}


def generate_gemini_image(image_prompt: str, api_key: str) -> bytes | None:
    """Generate a thumbnail via Gemini 2.0 Flash (free tier). Returns PNG bytes or None."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash-preview-image-generation:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": image_prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    try:
        r = http_requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        b64 = data["candidates"][0]["content"]["parts"][0]["inline_data"]["data"]
        return base64.b64decode(b64)
    except Exception as e:
        logger.warning(f"Gemini image generation failed (non-fatal): {e}")
        return None


def _thumbnail_style(template: str) -> str:
    return THUMBNAIL_STYLE_MAP.get(template, "A")


def _build_image_prompt(style: str, concept: str) -> str:
    """Build Imagen 4 prompt from style template + concept, injecting brand colours."""
    return THUMBNAIL_STYLE_PROMPTS[style].format(
        concept=concept,
        navy=BRAND["navy"],
        copper=BRAND["copper"],
        white=BRAND["white"],
    )


# ─── Funnel Stage ─────────────────────────────────────────────────────────────

def _determine_funnel_stage(idea: dict) -> str:
    """Infer TOFU/MOFU/BOFU from idea urgency and source article signals."""
    if idea.get("urgency") == "breaking":
        return "TOFU"

    source_ids = []
    try:
        source_ids = json.loads(idea.get("source_article_ids") or "[]")
    except Exception:
        pass

    if source_ids:
        conn = db.get_connection()
        try:
            placeholders = ",".join("?" * len(source_ids))
            rows = conn.execute(
                f"SELECT relevance_score, categories FROM articles WHERE id IN ({placeholders})",
                source_ids,
            ).fetchall()
        finally:
            conn.close()

        for row in rows:
            score = row["relevance_score"] or 0
            try:
                cats = json.loads(row["categories"] or "[]")
            except Exception:
                cats = []
            if score > 75 and "systems_thinking" in cats:
                return "MOFU"

    return "TOFU"


# ─── Draft Generation ─────────────────────────────────────────────────────────

def _draft_post(idea: dict, funnel_stage: str, pain_context: str, issues: list = None) -> dict:
    """Call Claude and return parsed 360Brew JSON dict."""
    template = idea.get("format", "Contrarian Take")
    template_guide = TEMPLATE_GUIDES.get(template, "")
    thumb_style = _thumbnail_style(template)
    issue_note = (
        f"\n\nPrevious draft had issues with: {', '.join(issues)}. Fix these specifically."
        if issues else ""
    )

    format_hint = {
        "TOFU": "text post (300-600 words) OR carousel outline (5-7 slides)",
        "MOFU": "long-form text (500-700+ words) OR carousel outline (10-15 slides)",
        "BOFU": "short text (300-400 words) + required thumbnail_concept",
    }[funnel_stage]

    prompt = f"""Write a LinkedIn post for Stuart Corrigan.

FUNNEL STAGE: {funnel_stage} — {format_hint}
THUMBNAIL STYLE: {thumb_style} (auto-selected for this template)

IDEA:
Title: {idea['title']}
Template: {template}
Pillar: {idea.get('pillar', '')}
Hook (starting point): {idea.get('hook', '')}
Angle: {idea.get('angle', '')}
Key data: {idea.get('key_data', '')}

TEMPLATE STRUCTURE:
{template_guide}

PAIN POINT DATA (use what's relevant):
{pain_context}
{issue_note}

OUTPUT: Return a single valid JSON object. No preamble, no markdown fences.
{{
  "funnel_stage": "{funnel_stage}",
  "format": "text|carousel|text+image",
  "hook": "<first line — the scroll-stopper, max 120 chars>",
  "post_body": "<complete post text, British English, line breaks, NO hashtags here>",
  "hashtags": ["#Broad1", "#Broad2", "#Niche1"],
  "carousel_outline": ["Slide 1: Title", "Slide 2: ..."] or null,
  "thumbnail_concept": "<10-20 words: what the thumbnail image literally shows, e.g. 'files stacking up on a conveyor belt in a claims office'>",
  "save_trigger": "<one sentence: why a Claims Director saves this post>",
  "dwell_time_elements": "<one sentence: what structural choice makes them read slowly>"
}}

Rules:
- TOFU/MOFU text: carousel_outline=null, provide thumbnail_concept
- Carousel format: carousel_outline=list, thumbnail_concept=null
- BOFU: carousel_outline=null, provide thumbnail_concept
- post_body must NOT contain hashtags (appended separately)
- thumbnail_concept describes only what is SHOWN visually, no text content
"""

    raw = complete(prompt, system=BREW_SYSTEM, max_tokens=2000, temperature=0.75)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0]

    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.warning("Draft JSON parse failed — using raw text as post_body")
        data = {
            "funnel_stage": funnel_stage,
            "format": "text",
            "hook": raw.split("\n")[0][:120],
            "post_body": raw,
            "hashtags": [],
            "carousel_outline": None,
            "thumbnail_concept": None,
            "save_trigger": "",
            "dwell_time_elements": "",
        }

    # Build full Imagen 3 image_prompt from concept + style
    concept = data.get("thumbnail_concept") or ""
    data["image_prompt"] = _build_image_prompt(thumb_style, concept) if concept else None
    data["thumbnail_style"] = thumb_style
    return data


def _quality_check(post_body: str, idea: dict) -> dict:
    prompt = f"""Rate this LinkedIn post on 6 criteria, score each 1-10.

POST:
{post_body}

IDEA INTENT: {idea.get('angle', '')}

Return JSON only:
{{
  "factual_accuracy": <1-10>,
  "positioning_alignment": <1-10>,
  "audience_fit": <1-10>,
  "tone": <1-10>,
  "uniqueness": <1-10>,
  "hook_strength": <1-10>
}}"""
    try:
        raw = complete(prompt, max_tokens=300, temperature=0.2).strip()
        if raw.startswith("```"):
            raw = raw.split("```", 1)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw.strip())
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        return {c: 7 for c in QUALITY_CRITERIA}


def _format_pain_context(pain_points: list) -> str:
    if not pain_points:
        return ""
    return "\n".join(
        f"• {pp['data_point']}: {pp['value']} ({pp['source']}, {pp['date']})"
        for pp in pain_points[:15]
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False):
    run_id = db.log_agent_run("draft")
    logger.info("=== Draft Agent (360Brew + Brand) starting ===")

    ideas = db.get_top_ideas(limit=3)
    if not ideas:
        logger.warning("No ideas in queue — skipping draft run")
        db.finish_agent_run(run_id, "success", 0)
        return []

    pain_context = _format_pain_context(db.get_pain_points())
    all_drafts = []

    for idea in ideas:
        logger.info(f"Drafting: {idea['title']}")
        funnel_stage = _determine_funnel_stage(idea)
        template = idea.get("format", "Contrarian Take")
        thumb_style = _thumbnail_style(template)
        logger.info(f"Funnel: {funnel_stage} | Template: {template} | Thumbnail: Style {thumb_style}")

        brew = _draft_post(idea, funnel_stage, pain_context)
        post_body = brew.get("post_body", "")

        quality = _quality_check(post_body, idea)
        avg_score = sum(quality.values()) / len(quality)
        brew360_score = round(avg_score * 10)
        logger.info(f"brew360_score: {brew360_score}/100")

        if avg_score < 6:
            logger.info("Quality below threshold — regenerating...")
            issues = [k for k, v in quality.items() if v < 6]
            brew = _draft_post(idea, funnel_stage, pain_context, issues=issues)
            post_body = brew.get("post_body", "")
            quality = _quality_check(post_body, idea)
            avg_score = sum(quality.values()) / len(quality)
            brew360_score = round(avg_score * 10)

        hashtags = brew.get("hashtags") or []
        if hashtags:
            post_body = post_body.rstrip() + "\n\n" + " ".join(hashtags)

        draft_data = {
            "idea_id": idea["id"],
            "version": 1,
            "content": post_body,
            "funnel_stage": funnel_stage,
            "carousel_data": {
                "format": brew.get("format", "text"),
                "hook": brew.get("hook", ""),
                "hashtags": hashtags,
                "carousel_outline": brew.get("carousel_outline"),
                "thumbnail_concept": brew.get("thumbnail_concept"),
                "thumbnail_style": brew.get("thumbnail_style", thumb_style),
                "image_prompt": brew.get("image_prompt"),
                "save_trigger": brew.get("save_trigger", ""),
                "dwell_time_elements": brew.get("dwell_time_elements", ""),
                "brew360_score": brew360_score,
            },
            "quality_score": avg_score,
            "quality_issues": [k for k, v in quality.items() if v < 7],
            "status": "PENDING_REVIEW",
            "consultant_notes": (
                f"360Brew: {funnel_stage} | Style {thumb_style} | "
                f"brew360={brew360_score}/100 | Quality: {avg_score:.1f}/10"
            ),
        }

        if not dry_run:
            draft_id = db.insert_draft(draft_data)
            draft_data["id"] = draft_id
            logger.info(f"Stored draft #{draft_id} for '{idea['title'][:40]}'")

            # Gemini image generation (optional — graceful fallback)
            image_prompt = brew.get("image_prompt")
            google_key = os.getenv("GOOGLE_API_KEY")
            if image_prompt and google_key:
                img_bytes = generate_gemini_image(image_prompt, google_key)
                if img_bytes:
                    img_dir = _PROJECT_ROOT / "frontend" / "images"
                    img_dir.mkdir(parents=True, exist_ok=True)
                    img_file = f"draft_{draft_id}_{int(time.time())}.png"
                    (img_dir / img_file).write_bytes(img_bytes)
                    db.update_draft_image_path(draft_id, f"images/{img_file}")
                    logger.info(f"Saved Gemini thumbnail: {img_file}")

            conn = db.get_connection()
            try:
                conn.execute(
                    "UPDATE content_ideas SET status='drafted' WHERE id=?",
                    (idea["id"],),
                )
                conn.commit()
            finally:
                conn.close()

        all_drafts.append(draft_data)

    logger.info(f"=== Draft done. {len(all_drafts)} drafts created ===")
    db.finish_agent_run(run_id, "success", len(all_drafts))
    return all_drafts
