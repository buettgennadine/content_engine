"""
FastAPI endpoints for the Visual Agent.
Add these routes to your existing FastAPI app.

Usage in main.py:
    from api.visual_routes import router as visual_router
    app.include_router(visual_router, prefix="/api")
"""

import os
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(tags=["visuals"])

DB_PATH = os.getenv("DB_PATH", "data/content_engine.db")
VISUAL_DIR = Path(os.getenv("ENGINE_BASE_DIR", "/opt/descartes-engine")) / "data" / "visuals"


# ─── Request Models ──────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    draft_id: int
    override_type: str | None = None


class StatusUpdate(BaseModel):
    status: str  # 'approved' | 'rejected'


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/visuals/{draft_id}")
async def get_visuals(draft_id: int):
    """Get all visuals for a draft."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM visuals WHERE draft_id = ? ORDER BY slide_number ASC",
            (draft_id,)
        ).fetchall()

        if not rows:
            raise HTTPException(404, f"No visuals found for draft {draft_id}")

        return {
            "draft_id": draft_id,
            "count": len(rows),
            "visuals": [dict(r) for r in rows],
        }
    finally:
        conn.close()


@router.get("/visuals/{draft_id}/thumbnail")
async def get_thumbnail(draft_id: int):
    """Get the thumbnail image for a draft."""
    filepath = VISUAL_DIR / str(draft_id) / "thumbnail.png"
    if not filepath.exists():
        raise HTTPException(404, "Thumbnail not found")
    return FileResponse(str(filepath), media_type="image/png")


@router.get("/visuals/{draft_id}/slides")
async def get_slides(draft_id: int):
    """Get carousel slide images for a draft."""
    slide_dir = VISUAL_DIR / str(draft_id)
    if not slide_dir.exists():
        raise HTTPException(404, "No slides found")

    slides = sorted(slide_dir.glob("slide_*.png"))
    if not slides:
        raise HTTPException(404, "No carousel slides found")

    return {
        "draft_id": draft_id,
        "count": len(slides),
        "slides": [
            {
                "number": i + 1,
                "url": f"/api/visuals/{draft_id}/slide/{i + 1}",
                "filename": s.name,
            }
            for i, s in enumerate(slides)
        ],
    }


@router.get("/visuals/{draft_id}/slide/{number}")
async def get_slide(draft_id: int, number: int):
    """Get a specific carousel slide image."""
    filepath = VISUAL_DIR / str(draft_id) / f"slide_{number:02d}.png"
    if not filepath.exists():
        raise HTTPException(404, f"Slide {number} not found")
    return FileResponse(str(filepath), media_type="image/png")


@router.post("/visual/generate")
async def generate_visual(request: GenerateRequest):
    """Generate visual(s) for a draft. Runs async."""
    from openai import AsyncOpenAI
    from agents.visual import VisualAgent

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(500, "OPENAI_API_KEY not configured")

    async def llm_gen(model, system, user):
        client = AsyncOpenAI(api_key=openai_key)
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=500, temperature=0.7,
        )
        return resp.choices[0].message.content

    agent = VisualAgent(
        db_path=DB_PATH,
        openai_client=AsyncOpenAI(api_key=openai_key),
        llm_generate=llm_gen,
    )

    draft = agent.get_draft_by_id(request.draft_id)
    if not draft:
        raise HTTPException(404, f"Draft {request.draft_id} not found")

    await agent.generate_for_draft(draft, override_type=request.override_type)

    return {"status": "ok", "draft_id": request.draft_id, "message": "Visual generation complete"}


@router.post("/visual/regenerate/{visual_id}")
async def regenerate_visual(visual_id: int):
    """Regenerate a specific visual."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM visuals WHERE id = ?", (visual_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"Visual {visual_id} not found")

        # Mark old as replaced
        conn.execute(
            "UPDATE visuals SET status = 'replaced' WHERE id = ?",
            (visual_id,)
        )
        conn.commit()
    finally:
        conn.close()

    # Trigger regeneration for the draft
    request = GenerateRequest(draft_id=row["draft_id"])
    return await generate_visual(request)


@router.patch("/visuals/{visual_id}")
async def update_visual_status(visual_id: int, update: StatusUpdate):
    """Update visual status (approve/reject)."""
    if update.status not in ("approved", "rejected"):
        raise HTTPException(400, "Status must be 'approved' or 'rejected'")

    conn = sqlite3.connect(DB_PATH)
    try:
        result = conn.execute(
            "UPDATE visuals SET status = ? WHERE id = ?",
            (update.status, visual_id)
        )
        if result.rowcount == 0:
            raise HTTPException(404, f"Visual {visual_id} not found")
        conn.commit()
        return {"status": "ok", "visual_id": visual_id, "new_status": update.status}
    finally:
        conn.close()
