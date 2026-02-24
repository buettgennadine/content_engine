"""
FastAPI Layer — Descartes Content Engine
Exposes SQLite data to HTML Frontend.
Port 8000. Claude API Proxy (API key stays server-side).
"""

import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import anthropic

from core import database as db
from core.llm import chat as llm_chat

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Descartes Content Engine API",
    description="Intelligence Feed · Content Pipeline · Performance Dashboard",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()


# ─── Models ───────────────────────────────────────────────────────────────────

class DraftStatusUpdate(BaseModel):
    status: str  # APPROVED | REJECTED
    reason: Optional[str] = None
    feedback: Optional[str] = None
    scheduled_date: Optional[str] = None


class GenerateRequest(BaseModel):
    topic: str
    template: str = "Data Hook"
    pillar: str = "claims"
    audience: str = "Claims Directors, COOs"
    language: str = "EN"
    tone: str = "provocative"


class PerformanceEntry(BaseModel):
    post_id: Optional[int] = None
    date: str
    impressions: int
    engagement_rate: float
    saves: int
    comments: int
    template: str


# ─── Intelligence Feed ────────────────────────────────────────────────────────

@app.get("/api/feed")
def get_feed(category: Optional[str] = None, min_vps: float = 0, limit: int = 30):
    """All articles, scored, recent. Filter by category and min VPS."""
    articles = db.get_recent_articles(limit=limit, min_vps=min_vps)
    if category:
        articles = [
            a for a in articles
            if category in json.loads(a.get("categories", "[]"))
        ]
    # Parse JSON fields
    for a in articles:
        a["categories"] = _parse_json(a.get("categories", "[]"))
        a["data_points"] = _parse_json(a.get("data_points", "[]"))
        a["vps_breakdown"] = _parse_json(a.get("vps_breakdown", "{}"))
    return {"articles": articles, "count": len(articles)}


@app.get("/api/feed/{article_id}")
def get_article(article_id: int):
    """Single article detail with VPS breakdown and angle."""
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")
    article = dict(row)
    article["categories"] = _parse_json(article.get("categories", "[]"))
    article["data_points"] = _parse_json(article.get("data_points", "[]"))
    article["vps_breakdown"] = _parse_json(article.get("vps_breakdown", "{}"))
    article["analysis"] = _parse_json(article.get("analysis", "{}"))
    return article


# ─── Content Pipeline ─────────────────────────────────────────────────────────

@app.get("/api/ideas")
def get_ideas():
    """Content Ideas Queue, prioritised."""
    ideas = db.get_all_ideas()
    for idea in ideas:
        idea["source_article_ids"] = _parse_json(idea.get("source_article_ids", "[]"))
    return {"ideas": ideas, "count": len(ideas)}


@app.get("/api/drafts")
def get_drafts(status: Optional[str] = None):
    """Drafts with status filter. Default: all."""
    if status:
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT d.*, ci.title as idea_title FROM drafts d "
            "LEFT JOIN content_ideas ci ON d.idea_id=ci.id "
            "WHERE d.status=? ORDER BY d.created_at DESC",
            (status,)
        ).fetchall()
        conn.close()
        drafts = [dict(r) for r in rows]
    else:
        drafts = db.get_all_drafts()

    for d in drafts:
        d["quality_issues"] = _parse_json(d.get("quality_issues", "[]"))
        d["carousel_data"] = _parse_json(d.get("carousel_data", "{}"))
    return {"drafts": drafts, "count": len(drafts)}


@app.get("/api/drafts/{draft_id}")
def get_draft(draft_id: int):
    """Single draft detail."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft["quality_issues"] = _parse_json(draft.get("quality_issues", "[]"))
    draft["carousel_data"] = _parse_json(draft.get("carousel_data", "{}"))
    return draft


@app.patch("/api/drafts/{draft_id}")
def update_draft_status(draft_id: int, update: DraftStatusUpdate):
    """Stuart approves or rejects a draft."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    valid_statuses = {"APPROVED", "REJECTED", "PENDING_REVIEW"}
    if update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")

    db.update_draft_status(
        draft_id=draft_id,
        status=update.status,
        reason=update.reason,
        feedback=update.feedback
    )

    # Schedule if approved with date
    if update.status == "APPROVED" and update.scheduled_date:
        conn = db.get_connection()
        conn.execute(
            "UPDATE drafts SET scheduled_date=? WHERE id=?",
            (update.scheduled_date, draft_id)
        )
        conn.commit()
        conn.close()

    return {"success": True, "draft_id": draft_id, "new_status": update.status}


@app.post("/api/generate")
def generate_post(request: GenerateRequest):
    """
    On-demand post generation via Claude API (server-side proxy).
    API key never exposed to frontend.
    """
    pain_points = db.get_pain_points()
    pain_context = "\n".join([
        f"- {pp['data_point']}: {pp['value']}"
        for pp in pain_points[:15]
    ])

    lang_instruction = "Write in German (formal Sie form, Fach-Deutsch for insurance professionals)" \
        if request.language == "DE" else "Write in British English"

    system = f"""You are Stuart Corrigan writing LinkedIn posts for Descartes Consulting.
Voice: Direct, British, Systems Thinking practitioner. No jargon, no transformation theatre.
Attribution rule: Never blame individuals. Always frame as system design issues.
Banned words: transformation programme, digital transformation, journey, synergy, leverage, stakeholder engagement.
{lang_instruction}"""

    user = f"""Write a LinkedIn post.

Topic: {request.topic}
Template: {request.template}
Audience: {request.audience}
Tone: {request.tone}

Known pain points for context:
{pain_context}

Output ONLY the post. No explanations."""

    try:
        content = llm_chat(system, user, max_tokens=600, temperature=0.85)
        return {
            "success": True,
            "content": content,
            "template": request.template,
            "language": request.language
        }
    except Exception as e:
        logger.error(f"Generate endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# ─── Performance ──────────────────────────────────────────────────────────────

@app.get("/api/performance")
def get_performance():
    """LinkedIn performance metrics."""
    conn = db.get_connection()
    # Performance stored in drafts that are PUBLISHED with metrics
    published = conn.execute("""
        SELECT d.*, ci.title as idea_title, ci.pillar
        FROM drafts d
        LEFT JOIN content_ideas ci ON d.idea_id = ci.id
        WHERE d.status = 'PUBLISHED'
        ORDER BY d.scheduled_date DESC
    """).fetchall()
    conn.close()
    return {"published_posts": [dict(r) for r in published]}


# ─── System Status ────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_status():
    """Agent status, queue sizes, source health."""
    status = db.get_system_status()

    # Last run times from logs (approximate)
    conn = db.get_connection()
    last_article = conn.execute(
        "SELECT MAX(collected_date) FROM articles"
    ).fetchone()[0]
    last_briefing = conn.execute(
        "SELECT MAX(created_at) FROM briefings"
    ).fetchone()[0]
    broken_sources = conn.execute(
        "SELECT name FROM sources WHERE status='broken'"
    ).fetchall()
    conn.close()

    return {
        **status,
        "last_monitor_run": last_article,
        "last_briefing": last_briefing,
        "broken_sources": [r[0] for r in broken_sources],
    }


@app.get("/api/sources")
def get_sources():
    """All active sources with health status."""
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM sources ORDER BY tier, status, name"
    ).fetchall()
    conn.close()
    sources = []
    for r in rows:
        s = dict(r)
        s["default_categories"] = _parse_json(s.get("default_categories", "[]"))
        sources.append(s)
    return {"sources": sources, "count": len(sources)}


@app.get("/api/briefing")
def get_briefing():
    """Latest Weekly Intelligence Briefing."""
    briefing = db.get_latest_briefing()
    if not briefing:
        return {"briefing": None, "message": "No briefing generated yet. Run on Friday at 15:00."}
    briefing["top_stories"] = _parse_json(briefing.get("top_stories", "[]"))
    briefing["trend_watch"] = _parse_json(briefing.get("trend_watch", "[]"))
    briefing["next_week_priorities"] = _parse_json(briefing.get("next_week_priorities", "[]"))
    return {"briefing": briefing}


@app.get("/api/painpoints")
def get_pain_points(category: Optional[str] = None):
    """Pain point database."""
    pain_points = db.get_pain_points(category=category)
    return {"pain_points": pain_points, "count": len(pain_points)}


# ─── Agent Triggers (Nadine's manual control) ────────────────────────────────

@app.post("/api/run/monitor")
def run_monitor():
    """Manually trigger Monitor Agent."""
    try:
        from agents.monitor import run
        result = run()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run/analyse")
def run_analyse():
    """Manually trigger Analyse Agent."""
    try:
        from agents.analyse import run
        result = run()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run/ideate")
def run_ideate():
    """Manually trigger Ideate Agent."""
    try:
        from agents.ideate import run
        result = run()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run/draft")
def run_draft():
    """Manually trigger Draft Agent."""
    try:
        from agents.draft import run
        result = run()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run/briefing")
def run_briefing():
    """Manually trigger Briefing Agent."""
    try:
        from agents.briefing import run
        result = run()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json(value):
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


# ─── Static Frontend ─────────────────────────────────────────────────────────

_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/")
def serve_index():
    return FileResponse(_frontend_dir / "index.html")

app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
