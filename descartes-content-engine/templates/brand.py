"""
Descartes Consulting — Brand Design System for Visual Agent.
Shared constants for all Pillow template renderers.
"""

import os
from pathlib import Path
from PIL import ImageFont

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(os.getenv("ENGINE_BASE_DIR", "/opt/descartes-engine"))
FONT_DIR = BASE_DIR / "assets" / "fonts"
ASSET_DIR = BASE_DIR / "assets"
VISUAL_DIR = BASE_DIR / "data" / "visuals"

# ─── Colors ──────────────────────────────────────────────────────────────────
COLORS = {
    "cream":       "#FBF7F0",
    "navy":        "#1B2A4A",
    "copper":      "#CF5D16",
    "copper_soft": "#F5E6D0",
    "success":     "#2F7A2E",
    "urgent":      "#C53030",
    "text_muted":  "#8B8680",
    "white":       "#FFFFFF",
}

# RGBA tuples for Pillow overlay operations
RGBA = {
    "navy_overlay_60": (27, 42, 74, 153),
    "navy_overlay_40": (27, 42, 74, 102),
    "dark_overlay":    (0, 0, 0, 120),
}

# ─── Font Files ──────────────────────────────────────────────────────────────
FONT_FILES = {
    "heading":   "Fraunces-SemiBold.ttf",
    "heading_italic": "Fraunces-SemiBoldItalic.ttf",
    "body":      "Outfit-Regular.ttf",
    "body_bold": "Outfit-SemiBold.ttf",
    "mono":      "IBMPlexMono-Medium.ttf",
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
