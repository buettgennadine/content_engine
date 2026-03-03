#!/usr/bin/env python3
"""
Run the Visual Agent.

Usage:
    # Process all pending drafts (cron job)
    python run_visual.py

    # Generate for a specific draft (on-demand)
    python run_visual.py --draft-id 42

    # Force a specific visual type
    python run_visual.py --draft-id 42 --type thumbnail

    # Setup: create visuals table
    python run_visual.py --setup
"""

import argparse
import asyncio
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents.visual import VisualAgent, ensure_visuals_table

# ─── Config ──────────────────────────────────────────────────────────────────

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/content_engine.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/visual_agent.log", mode="a"),
    ],
)
logger = logging.getLogger("run_visual")


# ─── LLM Helper ─────────────────────────────────────────────────────────────

async def llm_generate(model: str, system: str, user: str) -> str:
    """Generate text via OpenAI API (for DALL-E prompt engineering)."""
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Visual Agent — Image generation for drafts")
    parser.add_argument("--draft-id", type=int, help="Process a specific draft")
    parser.add_argument("--type", choices=["carousel", "thumbnail", "data_visual", "quote_card"],
                        help="Force a specific visual type")
    parser.add_argument("--setup", action="store_true", help="Create visuals table in DB")
    args = parser.parse_args()

    # Setup mode
    if args.setup:
        ensure_visuals_table(DB_PATH)
        logger.info("Setup complete. Visuals table created.")
        return

    # Validate config
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set in environment")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        logger.error(f"Database not found: {DB_PATH}")
        sys.exit(1)

    # Ensure logs directory
    os.makedirs("logs", exist_ok=True)

    # Init OpenAI client
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    # Init agent
    agent = VisualAgent(
        db_path=DB_PATH,
        openai_client=openai_client,
        llm_generate=llm_generate,
    )

    if args.draft_id:
        # On-demand: specific draft
        draft = agent.get_draft_by_id(args.draft_id)
        if not draft:
            logger.error(f"Draft {args.draft_id} not found")
            sys.exit(1)

        await agent.generate_for_draft(draft, override_type=args.type)
        logger.info(f"Done. Visual generated for draft {args.draft_id}")
    else:
        # Cron mode: process all pending
        await agent.run_async()
        logger.info("Done. All pending drafts processed.")


if __name__ == "__main__":
    asyncio.run(main())
