"""
Pillow Quote Card Renderer.
Renders Stuart's quotes as branded visuals (1200x1200).
"""

import logging
from PIL import Image, ImageDraw

from templates.brand import (
    SIZES, get_rgb, load_font, get_avatar_path, get_visual_dir
)

logger = logging.getLogger(__name__)


def render_quote_card(
    quote: str,
    draft_id: int,
    funnel_stage: str = "tofu",
) -> str:
    """Render a quote card with large decorative quotes and attribution.

    Returns file path to generated PNG.
    """
    output_dir = get_visual_dir(draft_id)
    size = SIZES["square_visual"]  # (1200, 1200)

    bg_color = get_rgb("cream")
    text_color = get_rgb("navy")
    accent_color = get_rgb("copper")
    muted_color = get_rgb("text_muted")

    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    # ─── Decorative opening quote mark ───────────────────────────────
    quote_mark_font = load_font("heading", 160)
    draw.text((80, 140), "\u201C", font=quote_mark_font, fill=accent_color)

    # ─── Quote text ──────────────────────────────────────────────────
    quote_font = load_font("heading_italic", 40)
    _draw_wrapped_text(
        draw, quote, quote_font, text_color,
        x=100, y=340, max_width=1000, line_spacing=18
    )

    # ─── Decorative closing quote mark ───────────────────────────────
    # Position based on estimated text height
    words = quote.split()
    estimated_lines = max(1, len(words) // 6)
    close_y = 340 + (estimated_lines * 65) + 30
    close_y = min(close_y, 780)  # Cap position

    bbox = quote_mark_font.getbbox("\u201D")
    mark_width = bbox[2] - bbox[0]
    draw.text(
        (size[0] - mark_width - 80, close_y),
        "\u201D",
        font=quote_mark_font,
        fill=accent_color
    )

    # ─── Divider ─────────────────────────────────────────────────────
    divider_y = 900
    draw.rectangle([(100, divider_y), (1100, divider_y + 2)], fill=get_rgb("copper_soft"))

    # ─── Avatar + Attribution ────────────────────────────────────────
    attr_y = divider_y + 40
    avatar_path = get_avatar_path()

    if avatar_path.exists():
        try:
            avatar = Image.open(str(avatar_path)).resize((70, 70))
            # Circular mask
            mask = Image.new("L", (70, 70), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 70, 70), fill=255)
            img.paste(avatar, (100, attr_y), mask)

            text_x = 190
        except Exception as e:
            logger.warning(f"Could not load avatar: {e}")
            text_x = 100
    else:
        text_x = 100

    name_font = load_font("body_bold", 24)
    role_font = load_font("body", 20)

    draw.text((text_x, attr_y + 8), "Stuart Corrigan", font=name_font, fill=text_color)
    draw.text((text_x, attr_y + 40), "Descartes Consulting", font=role_font, fill=muted_color)

    # ─── Save ────────────────────────────────────────────────────────
    filepath = output_dir / "quote_card.png"
    img.save(str(filepath), "PNG", quality=95)
    logger.info(f"Rendered quote card: {filepath}")
    return str(filepath)


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    color: tuple,
    x: int,
    y: int,
    max_width: int,
    line_spacing: int = 10,
) -> int:
    """Draw text with word wrapping. Returns Y after last line."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=color)
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        current_y += line_height + line_spacing

    return current_y
