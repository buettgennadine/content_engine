"""
Agent 6: Visual — Generates LinkedIn-optimised images for drafts.

Hybrid approach:
- Pillow templates for text-based visuals (carousels, data visuals, quote cards)
- DALL-E 3 for photographic/metaphorical thumbnails

Trigger: Automatically after Draft Agent, or on-demand via API.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from core.content_parser import ContentParser
from templates.pillow_carousel import render_carousel
from templates.pillow_data import render_data_visual
from templates.pillow_quote import render_quote_card
from templates.pillow_thumbnail import render_thumbnail

logger = logging.getLogger(__name__)


class VisualAgent:
    """Generates visuals for LinkedIn drafts based on post type and funnel stage."""

    def __init__(self, db_path: str, openai_client=None, llm_generate=None):
        """
        Args:
            db_path: Path to SQLite database
            openai_client: OpenAI async client (for DALL-E 3)
            llm_generate: Async function for LLM calls (GPT-4o-mini)
        """
        self.db_path = db_path
        self.openai_client = openai_client
        self.llm_generate = llm_generate
        self.parser = ContentParser()

    def run(self):
        """Synchronous entry point for cron jobs."""
        asyncio.run(self.run_async())

    async def run_async(self):
        """Process all drafts that need visuals."""
        drafts = self._get_pending_drafts()

        if not drafts:
            logger.info("No drafts pending visual generation.")
            return

        logger.info(f"Processing {len(drafts)} drafts for visual generation.")

        for draft in drafts:
            try:
                await self.generate_for_draft(draft)
            except Exception as e:
                logger.error(f"Failed to generate visual for draft {draft['id']}: {e}")
                self._update_visual_status(draft["id"], "error")

    async def generate_for_draft(self, draft: dict, override_type: str | None = None):
        """Generate visual(s) for a single draft.

        Args:
            draft: Dict with keys: id, content, post_type, funnel_stage, carousel_data, idea_id
            override_type: Force a specific visual type (for on-demand)
        """
        draft_id = draft["id"]
        post_type = draft.get("post_type", "text")
        funnel_stage = draft.get("funnel_stage", "tofu").lower()
        content = draft.get("content", "")
        carousel_data = draft.get("carousel_data")

        logger.info(
            f"Generating visual for draft {draft_id} "
            f"(type={post_type}, funnel={funnel_stage})"
        )

        # Determine visual type
        if override_type:
            visual_type = override_type
        else:
            visual_type = self.parser.detect_visual_type(content, post_type, carousel_data)

        if visual_type == "none":
            logger.info(f"Draft {draft_id}: no visual needed (post_type={post_type})")
            self._update_visual_status(draft_id, "no_visual")
            return

        # Route to correct generator
        paths = []

        if visual_type == "carousel":
            paths = await self._generate_carousel(draft_id, carousel_data, content, funnel_stage)

        elif visual_type == "thumbnail":
            path = await self._generate_thumbnail(draft_id, content, funnel_stage)
            paths = [path]

        elif visual_type == "data_visual":
            path = await self._generate_data_visual(draft_id, content, funnel_stage)
            if path:
                paths = [path]

        elif visual_type == "quote_card":
            path = await self._generate_quote_card(draft_id, content, funnel_stage)
            paths = [path]

        # Store results in DB
        if paths:
            self._store_visuals(draft_id, visual_type, paths, funnel_stage)
            self._update_visual_status(draft_id, "generated")
            logger.info(f"Draft {draft_id}: generated {len(paths)} visual(s)")
        else:
            self._update_visual_status(draft_id, "no_visual")

    # ─── Generators ──────────────────────────────────────────────────────────

    async def _generate_carousel(
        self, draft_id: int, carousel_data, content: str, funnel_stage: str
    ) -> list[str]:
        """Generate carousel slide images."""
        slides = self.parser.parse_carousel_slides(carousel_data)

        if not slides:
            # Try parsing from content if carousel_data is empty
            logger.warning(f"Draft {draft_id}: no carousel_data, attempting content parse")
            slides = self.parser.parse_carousel_slides(content)

        if not slides:
            logger.warning(f"Draft {draft_id}: could not parse carousel slides")
            return []

        return render_carousel(slides, draft_id, funnel_stage)

    async def _generate_thumbnail(
        self, draft_id: int, content: str, funnel_stage: str
    ) -> str:
        """Generate thumbnail with DALL-E background + text overlay."""
        headline = self.parser.extract_headline(content, max_words=8)

        return await render_thumbnail(
            headline=headline,
            draft_id=draft_id,
            draft_content=content,
            funnel_stage=funnel_stage,
            openai_client=self.openai_client,
            llm_generate=self.llm_generate,
        )

    async def _generate_data_visual(
        self, draft_id: int, content: str, funnel_stage: str
    ) -> str | None:
        """Generate data visual if content contains a prominent number."""
        data = self.parser.extract_key_number(content)
        if not data:
            logger.info(f"Draft {draft_id}: no prominent number found for data visual")
            return None

        return render_data_visual(data, draft_id, funnel_stage)

    async def _generate_quote_card(
        self, draft_id: int, content: str, funnel_stage: str
    ) -> str:
        """Generate a quote card from the strongest sentence."""
        quote = self.parser.extract_hook_quote(content, max_words=25)
        return render_quote_card(quote, draft_id, funnel_stage)

    # ─── Database ────────────────────────────────────────────────────────────

    def _get_pending_drafts(self) -> list[dict]:
        """Get drafts that need visual generation."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("""
                SELECT d.id, d.content, d.carousel_data, d.visual_status,
                       i.format as post_type, i.pillar as funnel_stage
                FROM drafts d
                LEFT JOIN content_ideas i ON d.idea_id = i.id
                WHERE d.status = 'PENDING_REVIEW'
                  AND (d.visual_status = 'pending' OR d.visual_status IS NULL)
                ORDER BY d.id DESC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def _store_visuals(
        self, draft_id: int, visual_type: str, paths: list[str], funnel_stage: str
    ):
        """Store generated visual records in DB."""
        conn = sqlite3.connect(self.db_path)
        try:
            for i, path in enumerate(paths):
                # Determine specific type and generator
                if visual_type == "carousel":
                    record_type = "carousel_slide"
                    generator = "pillow_carousel"
                    slide_number = i + 1
                elif visual_type == "thumbnail":
                    record_type = "thumbnail"
                    generator = "dalle3_pillow"
                    slide_number = None
                elif visual_type == "data_visual":
                    record_type = "data_visual"
                    generator = "pillow_data"
                    slide_number = None
                elif visual_type == "quote_card":
                    record_type = "quote_card"
                    generator = "pillow_quote"
                    slide_number = None
                else:
                    record_type = visual_type
                    generator = "unknown"
                    slide_number = None

                conn.execute("""
                    INSERT INTO visuals
                        (draft_id, type, generator, file_path, slide_number,
                         funnel_stage, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'generated', ?)
                """, (
                    draft_id, record_type, generator, path,
                    slide_number, funnel_stage, datetime.utcnow().isoformat()
                ))

            conn.commit()
        finally:
            conn.close()

    def _update_visual_status(self, draft_id: int, status: str):
        """Update draft's visual_status field."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE drafts SET visual_status = ? WHERE id = ?",
                (status, draft_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_draft_by_id(self, draft_id: int) -> dict | None:
        """Fetch a single draft by ID (for on-demand generation)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("""
                SELECT d.id, d.content, d.carousel_data, d.visual_status,
                       i.format as post_type, i.pillar as funnel_stage
                FROM drafts d
                LEFT JOIN content_ideas i ON d.idea_id = i.id
                WHERE d.id = ?
            """, (draft_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


def ensure_visuals_table(db_path: str):
    """Create the visuals table if it doesn't exist. Run once on setup."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visuals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                generator TEXT NOT NULL,
                file_path TEXT NOT NULL,
                dalle_prompt TEXT,
                slide_number INTEGER,
                funnel_stage TEXT,
                status TEXT DEFAULT 'generated',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (draft_id) REFERENCES drafts(id)
            )
        """)

        # Add visual_status to drafts if not exists
        try:
            conn.execute("ALTER TABLE drafts ADD COLUMN visual_status TEXT DEFAULT 'pending'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        logger.info("Visuals table ensured.")
    finally:
        conn.close()
