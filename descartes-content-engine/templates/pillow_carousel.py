"""
Pillow Carousel Renderer.
Converts carousel text data into branded slide images (1080x1080).
"""

import logging
from pathlib import Path
from PIL import Image, ImageDraw

from templates.brand import (
    SIZES, COLORS, FUNNEL_STYLES,
    get_rgb, load_font, get_avatar_path, get_visual_dir
)
from core.content_parser import CarouselSlide

logger = logging.getLogger(__name__)

SLIDE_SIZE = SIZES["carousel_slide"]  # (1080, 1080)


def render_carousel(
    slides: list[CarouselSlide],
    draft_id: int,
    funnel_stage: str = "tofu",
) -> list[str]:
    """Render a complete carousel from slide data.

    Returns list of file paths to generated PNGs.
    """
    output_dir = get_visual_dir(draft_id)
    total = len(slides)
    paths = []

    style = FUNNEL_STYLES.get(funnel_stage, FUNNEL_STYLES["tofu"])

    for slide in slides:
        if slide.slide_type == "cover":
            img = _render_cover(slide, total, style)
        elif slide.slide_type == "cta":
            img = _render_cta(slide, total, style)
        else:
            img = _render_content(slide, total, style)

        filename = f"slide_{slide.number:02d}.png"
        filepath = output_dir / filename
        img.save(str(filepath), "PNG", quality=95)
        paths.append(str(filepath))
        logger.info(f"Rendered slide {slide.number}/{total}: {filepath}")

    return paths


def _render_cover(slide: CarouselSlide, total: int, style: dict) -> Image.Image:
    """Render the cover slide (slide 1)."""
    bg_color = get_rgb(style["bg_primary"])
    text_color = get_rgb(style["text_primary"])
    accent_color = get_rgb(style["accent"])

    img = Image.new("RGB", SLIDE_SIZE, bg_color)
    draw = ImageDraw.Draw(img)

    # Accent line top
    draw.rectangle([(100, 200), (980, 203)], fill=accent_color)

    # Headline
    heading_font = load_font("heading", 52)
    _draw_wrapped_text(
        draw, slide.headline, heading_font, text_color,
        x=100, y=260, max_width=880, line_spacing=16
    )

    # Accent line bottom
    draw.rectangle([(100, 780), (980, 783)], fill=accent_color)

    # Author
    body_font = load_font("body", 22)
    draw.text((100, 830), "Stuart Corrigan", font=body_font, fill=text_color)
    muted = get_rgb("text_muted")
    small_font = load_font("body", 18)
    draw.text((100, 860), "Descartes Consulting", font=small_font, fill=muted)

    # Slide number
    _draw_slide_number(draw, slide.number, total)

    return img


def _render_content(slide: CarouselSlide, total: int, style: dict) -> Image.Image:
    """Render a content slide (slides 2 to N-1)."""
    # Alternate backgrounds for visual rhythm
    if slide.number % 2 == 0:
        bg_color = get_rgb(style["bg_primary"])
        text_color = get_rgb(style["text_primary"])
    else:
        bg_color = get_rgb(style["bg_secondary"])
        # Invert text for dark backgrounds
        text_color = get_rgb("white") if style["bg_secondary"] == "navy" else get_rgb("navy")

    accent_color = get_rgb(style["accent"])

    img = Image.new("RGB", SLIDE_SIZE, bg_color)
    draw = ImageDraw.Draw(img)

    # Large slide number as visual anchor
    number_font = load_font("mono", 72)
    draw.text((100, 140), str(slide.number), font=number_font, fill=accent_color)

    # Main point
    heading_font = load_font("heading", 40)
    _draw_wrapped_text(
        draw, slide.headline, heading_font, text_color,
        x=100, y=280, max_width=880, line_spacing=14
    )

    # Supporting detail (if present)
    if slide.subtext:
        muted = get_rgb("text_muted")
        body_font = load_font("body", 24)
        _draw_wrapped_text(
            draw, slide.subtext, body_font, muted,
            x=100, y=580, max_width=880, line_spacing=10
        )

    # Slide number indicator
    _draw_slide_number(draw, slide.number, total)

    return img


def _render_cta(slide: CarouselSlide, total: int, style: dict) -> Image.Image:
    """Render the CTA slide (last slide)."""
    bg_color = get_rgb(style["bg_primary"])
    text_color = get_rgb(style["text_primary"])
    accent_color = get_rgb(style["accent"])

    img = Image.new("RGB", SLIDE_SIZE, bg_color)
    draw = ImageDraw.Draw(img)

    # "Key Takeaway:" label
    label_font = load_font("body_bold", 20)
    draw.text((100, 200), "Key Takeaway:", font=label_font, fill=accent_color)

    # Takeaway text
    heading_font = load_font("heading", 36)
    _draw_wrapped_text(
        draw, slide.headline, heading_font, text_color,
        x=100, y=270, max_width=880, line_spacing=14
    )

    # Divider
    draw.rectangle([(100, 640), (980, 641)], fill=get_rgb("text_muted"))

    # Follow CTA
    body_font = load_font("body", 22)
    draw.text((100, 690), "Follow Stuart Corrigan", font=body_font, fill=text_color)
    small_font = load_font("body", 18)
    muted = get_rgb("text_muted")
    draw.text(
        (100, 722),
        "for more on systems thinking in insurance operations.",
        font=small_font, fill=muted
    )

    # Avatar (if available)
    avatar_path = get_avatar_path()
    if avatar_path.exists():
        try:
            avatar = Image.open(str(avatar_path)).resize((60, 60))
            # Make circular
            mask = Image.new("L", (60, 60), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 60, 60), fill=255)
            img.paste(avatar, (100, 800), mask)
            draw.text((180, 810), "@stuartcorrigan", font=small_font, fill=muted)
        except Exception as e:
            logger.warning(f"Could not load avatar: {e}")

    # Slide number
    _draw_slide_number(draw, slide.number, total)

    return img


# ─── Helpers ─────────────────────────────────────────────────────────────────

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
    """Draw text with word wrapping. Returns Y position after last line."""
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


def _draw_slide_number(draw: ImageDraw.ImageDraw, current: int, total: int):
    """Draw slide number indicator in bottom right."""
    mono_font = load_font("mono", 16)
    text = f"{current}/{total}"
    bbox = mono_font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    draw.text(
        (SLIDE_SIZE[0] - text_width - 60, SLIDE_SIZE[1] - 60),
        text,
        font=mono_font,
        fill=get_rgb("text_muted")
    )
