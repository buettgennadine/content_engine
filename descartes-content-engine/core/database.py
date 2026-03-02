"""
SQLite wrapper — Single Source of Truth for Descartes Content Engine.
"""
import sqlite3
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_db_path() -> str:
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    db = os.getenv("DB_PATH", "data/content_engine.db")
    # Resolve relative paths against project root, not cwd
    if not os.path.isabs(db):
        db = str(_PROJECT_ROOT / db)
    return db


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'rss',
                tier INTEGER NOT NULL DEFAULT 2,
                frequency TEXT DEFAULT 'daily',
                default_categories TEXT DEFAULT '[]',
                status TEXT DEFAULT 'active',
                last_checked TEXT,
                error_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source_id INTEGER REFERENCES sources(id),
                published_date TEXT,
                collected_date TEXT DEFAULT (datetime('now')),
                snippet TEXT,
                relevance_score REAL DEFAULT 0,
                categories TEXT DEFAULT '[]',
                urgency TEXT DEFAULT 'evergreen',
                content_angle TEXT,
                data_points TEXT DEFAULT '[]',
                analysis TEXT DEFAULT '{}',
                vps_score REAL DEFAULT 0,
                status TEXT DEFAULT 'new'
            );

            CREATE TABLE IF NOT EXISTS content_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                format TEXT,
                pillar TEXT,
                hook TEXT,
                angle TEXT,
                key_data TEXT,
                source_article_ids TEXT DEFAULT '[]',
                priority_score REAL DEFAULT 0,
                urgency TEXT DEFAULT 'this_week',
                effort TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id INTEGER REFERENCES content_ideas(id),
                version INTEGER DEFAULT 1,
                content TEXT NOT NULL,
                carousel_data TEXT DEFAULT '{}',
                consultant_notes TEXT,
                quality_score REAL DEFAULT 0,
                quality_issues TEXT DEFAULT '[]',
                status TEXT DEFAULT 'PENDING_REVIEW',
                created_at TEXT DEFAULT (datetime('now')),
                reviewed_at TEXT,
                reviewer_comment TEXT,
                scheduled_date TEXT
            );

            CREATE TABLE IF NOT EXISTS trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                category TEXT,
                direction TEXT DEFAULT 'stable',
                frequency_30d INTEGER DEFAULT 0,
                frequency_90d INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pain_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_point TEXT NOT NULL,
                value TEXT,
                source TEXT,
                date TEXT,
                category TEXT,
                country TEXT DEFAULT 'UK',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS briefings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                top_stories TEXT DEFAULT '[]',
                trend_watch TEXT DEFAULT '[]',
                next_week_priorities TEXT DEFAULT '[]',
                opportunity_spotted TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                started_at TEXT DEFAULT (datetime('now')),
                finished_at TEXT,
                articles_processed INTEGER DEFAULT 0,
                error_message TEXT
            );
        """)
        conn.commit()
        # Migrations: add columns if missing (safe to run on existing DBs)
        for migration in [
            "ALTER TABLE articles ADD COLUMN vps_score REAL DEFAULT 0",
            "ALTER TABLE drafts ADD COLUMN funnel_stage TEXT DEFAULT 'TOFU'",
            "ALTER TABLE drafts ADD COLUMN image_path TEXT",
        ]:
            try:
                conn.execute(migration)
                conn.commit()
                logger.info(f"Migrated: {migration}")
            except sqlite3.OperationalError:
                pass  # column already exists
        logger.info("Database initialised.")
    finally:
        conn.close()


def update_vps_score(article_id: int, vps_score: float):
    """Persist calculated VPS score to the articles table."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE articles SET vps_score = ? WHERE id = ?",
            (vps_score, article_id)
        )
        conn.commit()
    finally:
        conn.close()


def upsert_source(name: str, url: str, source_type: str = "rss", tier: int = 2, categories: list = None):
    """Insert or update a source by URL."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO sources (name, url, source_type, tier, default_categories)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                name = excluded.name,
                source_type = excluded.source_type,
                tier = excluded.tier,
                default_categories = excluded.default_categories
        """, (name, url, source_type, tier, json.dumps(categories or [])))
        conn.commit()
    finally:
        conn.close()


def insert_pain_point(data_point: str, value: str, source: str, date: str, category: str, country: str = "UK"):
    """Insert a single pain point."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO pain_points (data_point, value, source, date, category, country)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data_point, value, source, date, category, country))
        conn.commit()
    finally:
        conn.close()


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def article_exists(url: str) -> bool:
    conn = get_connection()
    try:
        h = url_hash(url)
        row = conn.execute("SELECT id FROM articles WHERE url_hash = ?", (h,)).fetchone()
        return row is not None
    finally:
        conn.close()


def insert_article(data: dict) -> Optional[int]:
    """Insert article. Returns new id or None if duplicate."""
    conn = get_connection()
    try:
        h = url_hash(data["url"])
        conn.execute("""
            INSERT OR IGNORE INTO articles
            (url_hash, title, url, source_id, published_date, snippet,
             relevance_score, categories, urgency, content_angle, data_points)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            h,
            data.get("title", ""),
            data["url"],
            data.get("source_id"),
            data.get("published_date"),
            data.get("snippet", "")[:500],
            data.get("relevance_score", 0),
            json.dumps(data.get("categories", [])),
            data.get("urgency", "evergreen"),
            data.get("content_angle"),
            json.dumps(data.get("data_points", [])),
        ))
        conn.commit()
        row = conn.execute("SELECT id FROM articles WHERE url_hash = ?", (h,)).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def get_recent_articles(hours: int = 24, min_score: float = 6.0, limit: int = 100, min_vps: float = 0) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT a.*, s.name as source_name, s.tier
            FROM articles a
            LEFT JOIN sources s ON a.source_id = s.id
            WHERE a.relevance_score >= ?
            ORDER BY a.relevance_score DESC
            LIMIT ?
        """, (min_score, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_week_articles(min_score: float = 7.0) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT a.*, s.name as source_name, s.tier
            FROM articles a
            LEFT JOIN sources s ON a.source_id = s.id
            WHERE a.collected_date >= datetime('now', '-7 days')
            AND a.relevance_score >= ?
            ORDER BY a.relevance_score DESC
        """, (min_score,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_active_sources(source_type: Optional[str] = None) -> list[dict]:
    conn = get_connection()
    try:
        if source_type:
            rows = conn.execute(
                "SELECT * FROM sources WHERE status = 'active' AND source_type = ? ORDER BY tier",
                (source_type,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sources WHERE status = 'active' ORDER BY tier"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_source_status(source_id: int, success: bool, error_msg: str = None):
    conn = get_connection()
    try:
        if success:
            conn.execute("""
                UPDATE sources SET last_checked = datetime('now'), error_count = 0
                WHERE id = ?
            """, (source_id,))
        else:
            conn.execute("""
                UPDATE sources
                SET last_checked = datetime('now'),
                    error_count = error_count + 1,
                    status = CASE WHEN error_count + 1 >= 3 THEN 'paused' ELSE status END
                WHERE id = ?
            """, (source_id,))
            logger.warning(f"Source {source_id} error: {error_msg}")
        conn.commit()
    finally:
        conn.close()


def get_pain_points(category: Optional[str] = None) -> list[dict]:
    conn = get_connection()
    try:
        if category:
            rows = conn.execute(
                "SELECT * FROM pain_points WHERE category = ? ORDER BY date DESC",
                (category,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM pain_points ORDER BY category, date DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def insert_idea(data: dict) -> int:
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO content_ideas
            (title, format, pillar, hook, angle, key_data, source_article_ids, priority_score, urgency, effort)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("title", ""),
            data.get("format", ""),
            data.get("pillar", ""),
            data.get("hook", ""),
            data.get("angle", ""),
            data.get("key_data", ""),
            json.dumps(data.get("source_article_ids", [])),
            data.get("priority_score", 0),
            data.get("urgency", "this_week"),
            data.get("effort", "medium"),
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_top_ideas(limit: int = 3) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM content_ideas
            WHERE status = 'pending'
            ORDER BY priority_score DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def insert_draft(data: dict) -> int:
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO drafts
            (idea_id, version, content, carousel_data, consultant_notes,
             quality_score, quality_issues, status, funnel_stage)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            data.get("idea_id"),
            data.get("version", 1),
            data.get("content", ""),
            json.dumps(data.get("carousel_data", {})),
            data.get("consultant_notes", ""),
            data.get("quality_score", 0),
            json.dumps(data.get("quality_issues", [])),
            data.get("status", "PENDING_REVIEW"),
            data.get("funnel_stage", "TOFU"),
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_draft_image_path(draft_id: int, image_path: str):
    conn = get_connection()
    try:
        conn.execute("UPDATE drafts SET image_path=? WHERE id=?", (image_path, draft_id))
        conn.commit()
    finally:
        conn.close()


def get_pending_drafts() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT d.*, i.title as idea_title, i.pillar, i.format
            FROM drafts d
            LEFT JOIN content_ideas i ON d.idea_id = i.id
            WHERE d.status = 'PENDING_REVIEW'
            ORDER BY d.created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_draft_status(draft_id: int, status: str, comment: str = None, scheduled_date: str = None, reason: str = None, feedback: str = None):
    conn = get_connection()
    try:
        review_comment = comment or reason or feedback
        conn.execute("""
            UPDATE drafts
            SET status = ?, reviewed_at = datetime('now'), reviewer_comment = ?, scheduled_date = ?
            WHERE id = ?
        """, (status, review_comment, scheduled_date, draft_id))
        conn.commit()
    finally:
        conn.close()


def log_agent_run(agent: str) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO agent_runs (agent) VALUES (?)", (agent,)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def finish_agent_run(run_id: int, status: str = "success", articles: int = 0, error: str = None):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE agent_runs
            SET status = ?, finished_at = datetime('now'), articles_processed = ?, error_message = ?
            WHERE id = ?
        """, (status, articles, error, run_id))
        conn.commit()
    finally:
        conn.close()


def insert_briefing(data: dict) -> int:
    conn = get_connection()
    try:
        cur = conn.execute("""
            INSERT INTO briefings (week_start, top_stories, trend_watch, next_week_priorities, opportunity_spotted)
            VALUES (?,?,?,?,?)
        """, (
            data.get("week_start", datetime.now().strftime("%Y-%m-%d")),
            json.dumps(data.get("top_stories", [])),
            json.dumps(data.get("trend_watch", [])),
            json.dumps(data.get("next_week_priorities", [])),
            data.get("opportunity_spotted", ""),
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_latest_briefing() -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM briefings ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_ideas() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM content_ideas ORDER BY priority_score DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_drafts() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT d.*, ci.title as idea_title
            FROM drafts d
            LEFT JOIN content_ideas ci ON d.idea_id = ci.id
            ORDER BY d.created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_draft(draft_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT d.*, ci.title as idea_title
            FROM drafts d
            LEFT JOIN content_ideas ci ON d.idea_id = ci.id
            WHERE d.id = ?
        """, (draft_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_system_status() -> dict:
    conn = get_connection()
    try:
        article_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        idea_count = conn.execute("SELECT COUNT(*) FROM content_ideas").fetchone()[0]
        draft_count = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
        source_count = conn.execute("SELECT COUNT(*) FROM sources WHERE status='active'").fetchone()[0]
        last_run = conn.execute(
            "SELECT agent, started_at, status FROM agent_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return {
            "articles": article_count,
            "ideas": idea_count,
            "drafts": draft_count,
            "active_sources": source_count,
            "last_agent_run": dict(last_run) if last_run else None,
        }
    finally:
        conn.close()
