#!/usr/bin/env python3
"""Run Ideate Agent — generate 12 content ideas from week's signals."""
import sys, logging, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(override=True)

Path("data").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("data/ideate.log")]
)

from core.database import init_db
init_db()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from agents.ideate import run
    ideas = run(dry_run=args.dry_run)
    print(f"Ideate complete: {len(ideas)} ideas generated")
