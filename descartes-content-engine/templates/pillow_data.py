"""
Pillow Data Visual Renderer.
Renders prominent statistics as branded visuals (1200x1200).
"""

import logging
from PIL import Image, ImageDraw

from templates.brand import (
    SIZES, FUNNEL_STYLES, ATTRIBUTION_NAME, ATTRIBUTION_COMPANY,
    get_rgb, load_font, get_visual_dir
)
from core.content_parser import KeyNumber

logger = logging.getLogger(__name__)

def _layout():
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "prompts" / "visual_layout.json"
    if p.exists():
        try:
            return json.load(open(p, encoding="utf-8")).get("data_visual", {})
        except Exception:
            pass
    return {}

_L = _layout()


def render_data_visual(
    data: KeyNumber,
    draft_id: int,
    funnel_stage: str = "tofu",
) -> str:
    """Render a data visual with prominent number + context.

    Returns file path to generated PNG.
    """
    output_dir = get_visual_dir(draft_id)
    size = SIZES["square_visual"]  # (1200, 1200)

    # Data visuals always use navy background for contrast
    bg_color = get_rgb("navy")
    number_color = get_rgb("copper")
    text_color = get_rgb("white")
    muted_color = get_rgb("text_muted")

    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    # ─── Main number ─────────────────────────────────────────────────
    number_font = load_font("mono", _L.get("font_size_number", 96))
    number_text = data.number

    # Center the number horizontally
    bbox = number_font.getbbox(number_text)
    number_width = bbox[2] - bbox[0]
    number_x = (size[0] - number_width) // 2
    draw.text((number_x, 320), number_text, font=number_font, fill=number_color)

    # ─── Change indicator (if present) ───────────────────────────────
    if data.change:
        change_font = load_font("mono", _L.get("font_size_change", 32))
        change_bbox = change_font.getbbox(data.change)
        change_width = change_bbox[2] - change_bbox[0]
        change_x = (size[0] - change_width) // 2

        # Color: green for positive, red for negative
        is_positive = data.change.startswith('+')
        change_color = get_rgb("success") if is_positive else get_rgb("urgent")
        draw.text((change_x, 440), data.change, font=change_font, fill=change_color)

    # ─── Context text ────────────────────────────────────────────────
    context_y = 520 if data.change else 460
    body_font = load_font("body", 28)

    # Word-wrap context
    _draw_centered_wrapped(
        draw, data.context, body_font, text_color,
        y=context_y, max_width=900, canvas_width=size[0], line_spacing=12
    )

    # ─── Divider ─────────────────────────────────────────────────────
    draw.rectangle([(400, 800), (800, 801)], fill=muted_color)

    # ─── Attribution ─────────────────────────────────────────────────
    name_font = load_font("body_bold", _L.get("font_size_attribution_name", 20))
    role_font = load_font("body", _L.get("font_size_attribution_role", 18))

    name_text = ATTRIBUTION_NAME
    role_text = ATTRIBUTION_COMPANY

    name_bbox = name_font.getbbox(name_text)
    name_w = name_bbox[2] - name_bbox[0]
    draw.text(((size[0] - name_w) // 2, 840), name_text, font=name_font, fill=text_color)

    role_bbox = role_font.getbbox(role_text)
    role_w = role_bbox[2] - role_bbox[0]
    draw.text(((size[0] - role_w) // 2, 870), role_text, font=role_font, fill=muted_color)

    # ─── Save ────────────────────────────────────────────────────────
    filepath = output_dir / "data_visual.png"
    img.save(str(filepath), "PNG", quality=95)
    logger.info(f"Rendered data visual: {filepath}")
    return str(filepath)


def _draw_centered_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    color: tuple,
    y: int,
    max_width: int,
    canvas_width: int,
    line_spacing: int = 10,
):
    """Draw word-wrapped text, centered horizontally."""
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
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        x = (canvas_width - line_width) // 2
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height + line_spacing
