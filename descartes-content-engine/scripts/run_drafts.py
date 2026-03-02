#!/usr/bin/env python3
"""Run Draft Agent — draft top 3 ideas as LinkedIn posts, generate images for BOFU."""
import sys
import os
import logging
import argparse
import base64
import requests as http_requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(override=True)

Path("data").mkdir(exist_ok=True)
Path("data/images").mkdir(exist_ok=True)
Path("data/assets").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("data/drafts.log")],
)

logger = logging.getLogger(__name__)

from core.database import init_db, update_draft_image_path
init_db()


def generate_imagen3(prompt: str, api_key: str) -> bytes:
    """Call Google Imagen 3 API. Returns PNG bytes."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/imagen-3.0-generate-001:predict?key={api_key}"
    )
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1},
    }
    resp = http_requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    b64 = data["predictions"][0]["bytesBase64Encoded"]
    return base64.b64decode(b64)


def composite_logo(base_path: Path, logo_path: Path, output_path: Path) -> None:
    """Composite logo_drcs onto base image: bottom-right, 12% of image width, 16px padding."""
    from PIL import Image

    base = Image.open(base_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    logo_w = int(base.width * 0.12)
    ratio = logo_w / logo.width
    logo_h = int(logo.height * ratio)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    padding = 16
    x = base.width - logo_w - padding
    y = base.height - logo_h - padding

    composite = base.copy()
    composite.paste(logo, (x, y), mask=logo)
    composite.convert("RGB").save(output_path, format="PNG")


def maybe_generate_image(draft: dict) -> None:
    """Generate Imagen 3 base image, composite logo, save thumbnail."""
    draft_id = draft.get("id")
    if not draft_id:
        return

    carousel_data = draft.get("carousel_data", {})
    image_prompt = carousel_data.get("image_prompt")
    if not image_prompt:
        return

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — skipping image generation")
        return

    try:
        logger.info(f"Generating image for draft #{draft_id}...")
        png_bytes = generate_imagen3(image_prompt, api_key)

        date_str = datetime.now().strftime("%Y%m%d")
        base_path = Path("data/images") / f"{draft_id}_{date_str}_base.png"
        base_path.write_bytes(png_bytes)

        thumbnail_path = Path("data/images") / f"{draft_id}_thumbnail.png"
        logo_path = Path("data/assets/logo_drcs.png")

        if logo_path.exists():
            composite_logo(base_path, logo_path, thumbnail_path)
            base_path.unlink()  # remove base, keep only composite
            final_path = thumbnail_path
            logger.info(f"Thumbnail with logo saved: {thumbnail_path}")
        else:
            # No logo available — use base image as-is
            base_path.rename(thumbnail_path)
            final_path = thumbnail_path
            logger.warning(f"logo_drcs.png not found at {logo_path} — using base image")

        update_draft_image_path(draft_id, str(final_path))
        logger.info(f"Image path updated: {final_path}")
    except Exception as e:
        logger.warning(f"Image generation failed for draft #{draft_id}: {e} — continuing")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from agents.draft import run
    drafts = run(dry_run=args.dry_run)

    if not args.dry_run:
        for draft in drafts:
            maybe_generate_image(draft)

    print(f"Draft complete: {len(drafts)} drafts created — status PENDING_REVIEW")
