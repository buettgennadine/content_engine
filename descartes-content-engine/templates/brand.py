"""
Quinn (Descartes Consulting) — Brand Design System for Visual Agent.
Shared constants for all Pillow template renderers.
Brand settings are loaded from prompts/visual_brand.json if present.
"""

import os
import json
import logging
from pathlib import Path
from PIL import ImageFont

logger = logging.getLogger(__name__)

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(os.getenv("ENGINE_BASE_DIR", "/opt/descartes-engine"))
FONT_DIR = BASE_DIR / "assets" / "fonts"
ASSET_DIR = BASE_DIR / "assets"
VISUAL_DIR = BASE_DIR / "data" / "visuals"

# ─── Load brand config from prompts/visual_brand.json ────────────────────────
def _load_brand_config() -> dict:
    config_path = Path(__file__).resolve().parent.parent / "prompts" / "visual_brand.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load visual_brand.json: {e}")
    return {}

_brand = _load_brand_config()

# ─── Colors ──────────────────────────────────────────────────────────────────
COLORS = {
    "cream":       "#F5E6CA",
    "navy":        "#111F32",
    "copper":      "#CF5D16",
    "copper_soft": "#F5E6CA",
    "success":     "#2F7A2E",
    "urgent":      "#C53030",
    "text_muted":  "#8B8680",
    "white":       "#FFFFFF",
}
COLORS.update(_brand.get("colors", {}))

# Attribution text
_attr = _brand.get("attribution", {})
ATTRIBUTION_NAME = _attr.get("name", "Stuart Corrigan")
ATTRIBUTION_COMPANY = _attr.get("company", "Descartes Consulting")
ATTRIBUTION_CTA = _attr.get("cta_follow", f"Follow {ATTRIBUTION_NAME}")

# RGBA tuples for Pillow overlay operations (derived from navy color)
def _navy_rgba(alpha: int) -> tuple:
    from templates.brand import hex_to_rgb  # avoid circular at module level
    r, g, b = hex_to_rgb(COLORS["navy"])
    return (r, g, b, alpha)

RGBA = {
    "navy_overlay_60": (17, 31, 50, 153),
    "navy_overlay_40": (17, 31, 50, 102),
    "dark_overlay":    (0, 0, 0, 120),
}

# ─── Font Files ──────────────────────────────────────────────────────────────
FONT_FILES = {
    "heading":        "Fraunces-SemiBold.ttf",
    "heading_italic": "Fraunces-SemiBoldItalic.ttf",
    "body":           "Outfit-Regular.ttf",
    "body_bold":      "Outfit-SemiBold.ttf",
    "mono":           "IBMPlexMono-Medium.ttf",
}

# ─── LinkedIn Sizes ──────────────────────────────────────────────────────────
SIZES = {
    "thumbnail":      (1200, 628),
    "carousel_slide": (1080, 1080),
    "square_visual":  (1200, 1200),
}

# ─── Funnel Stage Styles ────────────────────────────────────────────────────
FUNNEL_STYLES = {
    "tofu": {
        "label": "Awareness",
        "bg_primary": "navy",
        "bg_secondary": "copper",
        "text_primary": "white",
        "accent": "copper",
        "mood": "bold, provocative, high contrast",
    },
    "mofu": {
        "label": "Consideration",
        "bg_primary": "cream",
        "bg_secondary": "navy",
        "text_primary": "navy",
        "accent": "copper",
        "mood": "data-driven, analytical, structured",
    },
    "bofu": {
        "label": "Decision",
        "bg_primary": "cream",
        "bg_secondary": "copper_soft",
        "text_primary": "navy",
        "accent": "success",
        "mood": "trustworthy, warm, expert",
    },
}
# Merge funnel styles from config (only update keys that exist)
for stage, overrides in _brand.get("funnel_styles", {}).items():
    if stage in FUNNEL_STYLES:
        FUNNEL_STYLES[stage].update(overrides)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_color(name: str) -> str:
    """Get hex color by name."""
    return COLORS.get(name, COLORS["navy"])


def get_rgb(name: str) -> tuple[int, int, int]:
    """Get RGB tuple by color name."""
    return hex_to_rgb(get_color(name))


def load_font(style: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font by style name and size.

    Args:
        style: One of 'heading', 'heading_italic', 'body', 'body_bold', 'mono'
        size: Font size in points

    Returns:
        PIL ImageFont object

    Raises:
        FileNotFoundError if font file not found
    """
    filename = FONT_FILES.get(style)
    if not filename:
        raise ValueError(f"Unknown font style: {style}. Use: {list(FONT_FILES.keys())}")

    font_path = FONT_DIR / filename
    if not font_path.exists():
        raise FileNotFoundError(
            f"Font not found: {font_path}\n"
            f"Download from Google Fonts and place in {FONT_DIR}/"
        )

    return ImageFont.truetype(str(font_path), size)


def get_avatar_path() -> Path:
    """Get path to Stuart's avatar image."""
    return ASSET_DIR / "stuart_avatar.png"


def get_visual_dir(draft_id: int) -> Path:
    """Get/create output directory for a draft's visuals."""
    path = VISUAL_DIR / str(draft_id)
    path.mkdir(parents=True, exist_ok=True)
    return path
