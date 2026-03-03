"""
Prompt Editor API — read, write and version agent prompts.
All prompts live as .txt files in prompts/ directory.
Every save is versioned in the prompt_versions SQLite table.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["prompts"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = _PROJECT_ROOT / "prompts"
DB_PATH = os.getenv("DB_PATH", str(_PROJECT_ROOT / "data" / "content_engine.db"))


# ─── Prompt registry ────────────────────────────────────────────────────────

PROMPT_REGISTRY = [
    {"name": "draft_system",    "agent": "Draft",    "label": "System Prompt",       "file": "draft_system.txt"},
    {"name": "draft_user",      "agent": "Draft",    "label": "Post Generation",     "file": "draft_user.txt"},
    {"name": "quality_check",   "agent": "Draft",    "label": "Quality Check",       "file": "quality_check.txt"},
    {"name": "ideate_system",   "agent": "Ideate",   "label": "System Prompt",       "file": "ideate_system.txt"},
    {"name": "ideate_user",     "agent": "Ideate",   "label": "Idea Generation",     "file": "ideate_user.txt"},
    {"name": "analyse",         "agent": "Analyse",  "label": "Article Analysis",    "file": "analyse.txt"},
    {"name": "briefing_system", "agent": "Briefing", "label": "System Prompt",       "file": "briefing_system.txt"},
    {"name": "briefing_user",   "agent": "Briefing", "label": "Briefing Generation", "file": "briefing_user.txt"},
]

_registry_map = {p["name"]: p for p in PROMPT_REGISTRY}


# ─── DB helpers ─────────────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_name TEXT NOT NULL,
            content TEXT NOT NULL,
            edited_by TEXT DEFAULT 'nadine',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_active ON prompt_versions(prompt_name, is_active)")
    conn.commit()
    conn.close()


# ─── Models ─────────────────────────────────────────────────────────────────

class SaveRequest(BaseModel):
    content: str
    edited_by: str = "nadine"


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/prompts")
def list_prompts():
    """List all prompts with metadata."""
    _ensure_table()
    conn = _get_conn()
    result = []
    for p in PROMPT_REGISTRY:
        path = PROMPTS_DIR / p["file"]
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        # Last version from DB
        row = conn.execute(
            "SELECT created_at, edited_by FROM prompt_versions WHERE prompt_name=? ORDER BY id DESC LIMIT 1",
            (p["name"],)
        ).fetchone()
        result.append({
            "name": p["name"],
            "agent": p["agent"],
            "label": p["label"],
            "last_edited": row["created_at"] if row else None,
            "last_edited_by": row["edited_by"] if row else None,
            "char_count": len(content),
        })
    conn.close()
    return {"prompts": result}


@router.get("/prompts/{name}")
def get_prompt(name: str):
    """Get the current content of a prompt."""
    if name not in _registry_map:
        raise HTTPException(404, f"Prompt '{name}' not found")
    _ensure_table()
    meta = _registry_map[name]
    path = PROMPTS_DIR / meta["file"]
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    conn = _get_conn()
    row = conn.execute(
        "SELECT created_at, edited_by FROM prompt_versions WHERE prompt_name=? ORDER BY id DESC LIMIT 1",
        (name,)
    ).fetchone()
    conn.close()
    return {
        "name": name,
        "agent": meta["agent"],
        "label": meta["label"],
        "content": content,
        "last_edited": row["created_at"] if row else None,
        "last_edited_by": row["edited_by"] if row else None,
    }


@router.get("/prompts/{name}/history")
def get_prompt_history(name: str):
    """Get last 10 versions of a prompt."""
    if name not in _registry_map:
        raise HTTPException(404, f"Prompt '{name}' not found")
    _ensure_table()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, prompt_name, edited_by, created_at, substr(content,1,120) as preview "
        "FROM prompt_versions WHERE prompt_name=? ORDER BY id DESC LIMIT 10",
        (name,)
    ).fetchall()
    conn.close()
    return {"name": name, "history": [dict(r) for r in rows]}


@router.post("/prompts/{name}")
def save_prompt(name: str, req: SaveRequest):
    """Save a new version of a prompt (writes to disk + versions in DB)."""
    if name not in _registry_map:
        raise HTTPException(404, f"Prompt '{name}' not found")
    _ensure_table()
    meta = _registry_map[name]
    path = PROMPTS_DIR / meta["file"]
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(req.content, encoding="utf-8")

    conn = _get_conn()
    conn.execute(
        "INSERT INTO prompt_versions (prompt_name, content, edited_by, created_at) VALUES (?,?,?,?)",
        (name, req.content, req.edited_by, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return {"success": True, "name": name, "message": f"Prompt '{name}' saved."}


@router.post("/prompts/{name}/rollback/{version_id}")
def rollback_prompt(name: str, version_id: int):
    """Restore a specific historical version."""
    if name not in _registry_map:
        raise HTTPException(404, f"Prompt '{name}' not found")
    _ensure_table()
    conn = _get_conn()
    row = conn.execute(
        "SELECT content FROM prompt_versions WHERE id=? AND prompt_name=?",
        (version_id, name)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, f"Version {version_id} not found for prompt '{name}'")

    content = row["content"]
    meta = _registry_map[name]
    path = PROMPTS_DIR / meta["file"]
    path.write_text(content, encoding="utf-8")

    conn.execute(
        "INSERT INTO prompt_versions (prompt_name, content, edited_by, created_at) VALUES (?,?,?,?)",
        (name, content, "rollback", datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return {"success": True, "name": name, "restored_from": version_id}
