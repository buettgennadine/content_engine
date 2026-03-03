"""
Thumbnail Renderer.
Generates LinkedIn thumbnails: DALL-E 3 background + Pillow text overlay.
Fallback: branded gradient if DALL-E fails.
"""

import logging
import aiohttp
from pathlib import Path
from PIL import Image, ImageDraw

from templates.brand import (
    SIZES, RGBA, FUNNEL_STYLES,
    get_rgb, load_font, get_visual_dir
)

logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = SIZES["thumbnail"]  # (1200, 628)

# DALL-E uses different sizes — we resize afterwards
DALLE_SIZE = "1792x1024"


async def render_thumbnail(
    headline: str,
    draft_id: int,
    draft_content: str,
    funnel_stage: str,
    openai_client,
    llm_generate,
) -> str:
    """Generate a thumbnail: DALL-E background + text overlay.

    Args:
        headline: Short headline for overlay (max ~8 words)
        draft_id: Draft ID for file output
        draft_content: Full draft content for DALL-E prompt generation
        funnel_stage: 'tofu' | 'mofu' | 'bofu'
        openai_client: OpenAI async client
        llm_generate: async function to call GPT-4o-mini

    Returns:
        File path to generated PNG
    """
    output_dir = get_visual_dir(draft_id)

    try:
        # Step 1: Generate DALL-E prompt via GPT-4o-mini
        dalle_prompt = await _generate_dalle_prompt(
            draft_content, funnel_stage, llm_generate
        )

        # Step 2: Generate image via DALL-E 3
        bg_path = await _generate_dalle_image(
            dalle_prompt, draft_id, openai_client, output_dir
        )

        # Step 3: Apply text overlay
        filepath = output_dir / "thumbnail.png"
        _apply_overlay(bg_path, headline, funnel_stage, str(filepath))

        logger.info(f"Rendered thumbnail (DALL-E): {filepath}")
        return str(filepath)

    except Exception as e:
        logger.warning(f"DALL-E failed, using fallback gradient: {e}")
        filepath = output_dir / "thumbnail.png"
        _render_fallback(headline, funnel_stage, str(filepath))
        return str(filepath)


def _render_fallback(headline: str, funnel_stage: str, output_path: str):
    """Fallback: branded gradient background with text overlay."""
    style = FUNNEL_STYLES.get(funnel_stage, FUNNEL_STYLES["tofu"])
    bg_color = get_rgb(style["bg_primary"])
    accent = get_rgb(style["accent"])

    img = Image.new("RGB", THUMBNAIL_SIZE, bg_color)
    draw = ImageDraw.Draw(img)

    # Subtle gradient effect via rectangles
    for i in range(50):
        alpha = i / 50
        y = int(THUMBNAIL_SIZE[1] * 0.6 + (THUMBNAIL_SIZE[1] * 0.4 * alpha))
        r = int(bg_color[0] * (1 - alpha * 0.3))
        g = int(bg_color[1] * (1 - alpha * 0.3))
        b = int(bg_color[2] * (1 - alpha * 0.3))
        draw.rectangle([(0, y), (THUMBNAIL_SIZE[0], y + 5)], fill=(r, g, b))

    # Accent line
    draw.rectangle([(60, 100), (200, 104)], fill=accent)

    # Headline
    _draw_headline(draw, headline, style)

    # Footer
    _draw_footer(draw, style)

    img.save(output_path, "PNG", quality=95)
    logger.info(f"Rendered thumbnail (fallback): {output_path}")


async def _generate_dalle_prompt(
    draft_content: str,
    funnel_stage: str,
    llm_generate,
) -> str:
    """Use GPT-4o-mini to generate an optimised DALL-E prompt."""
    style = FUNNEL_STYLES.get(funnel_stage, FUNNEL_STYLES["tofu"])

    system_prompt = f"""You are a prompt engineer for LinkedIn thumbnail images.
Context: Management Consulting, Insurance/Pension Operations, UK/Germany.
Brand: Professional but not corporate-sterile. Warm, human, subtly provocative.

Rules:
- NO text in the image whatsoever (text is overlaid separately)
- No generic office look, no handshakes, no stock photo aesthetic
- Prefer: metaphors, systems, contrasts, abstract concepts
- Colour palette: warm (cream, copper, navy tones) where possible
- Format: 1792x1024 landscape, LinkedIn-optimised
- Style: photorealistic OR editorial illustration
- The image MUST have a calm area (lower third) for text overlay
- Mood: {style['mood']}

Funnel stage: {funnel_stage.upper()} ({style['label']})
- TOFU: Dramatic, provocative, high contrast
- MOFU: Analytical, structured, data-associated
- BOFU: Trustworthy, warm, competent

Generate ONE optimal DALL-E 3 prompt (max 200 words).
Ensure the image has enough calm space for a text overlay."""

    prompt = await llm_generate(
        model="gpt-4o-mini",
        system=system_prompt,
        user=f"Draft content:\n{draft_content[:1000]}\n\nGenerate the DALL-E prompt.",
    )

    return prompt.strip()


async def _generate_dalle_image(
    dalle_prompt: str,
    draft_id: int,
    openai_client,
    output_dir: Path,
) -> str:
    """Call DALL-E 3 and download the image."""
    response = await openai_client.images.generate(
        model="dall-e-3",
        prompt=dalle_prompt,
        size=DALLE_SIZE,
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    bg_path = str(output_dir / "bg_raw.png")

    # Download image
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status == 200:
                data = await resp.read()
                with open(bg_path, "wb") as f:
                    f.write(data)
            else:
                raise RuntimeError(f"DALL-E download failed: HTTP {resp.status}")

    logger.info(f"Downloaded DALL-E image: {bg_path}")
    return bg_path


def _apply_overlay(bg_path: str, headline: str, funnel_stage: str, output_path: str):
    """Apply semi-transparent overlay + text to DALL-E background."""
    style = FUNNEL_STYLES.get(funnel_stage, FUNNEL_STYLES["tofu"])

    # Load and resize DALL-E image
    bg = Image.open(bg_path).convert("RGBA")
    bg = bg.resize(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

    # Semi-transparent navy overlay
    overlay = Image.new("RGBA", THUMBNAIL_SIZE, RGBA["navy_overlay_60"])
    img = Image.alpha_composite(bg, overlay)

    # Convert to RGB for drawing
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Accent line
    accent = get_rgb(style["accent"])
    draw.rectangle([(60, 100), (200, 104)], fill=accent)

    # Headline (always white on dark overlay)
    _draw_headline(draw, headline, style, force_white=True)

    # Footer
    _draw_footer(draw, style, force_white=True)

    img.save(output_path, "PNG", quality=95)


def _draw_headline(draw, headline, style, force_white=False):
    """Draw headline text on thumbnail."""
    text_color = (255, 255, 255) if force_white else get_rgb(style["text_primary"])

    heading_font = load_font("heading", 52)
    words = headline.split()
    lines = []
    current_line = []

    for word in words:
        test = ' '.join(current_line + [word])
        bbox = heading_font.getbbox(test)
        if bbox[2] - bbox[0] <= 1060:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))

    y = 180
    for line in lines:
        draw.text((60, y), line, font=heading_font, fill=text_color)
        bbox = heading_font.getbbox(line)
        y += (bbox[3] - bbox[1]) + 14


def _draw_footer(draw, style, force_white=False):
    """Draw footer attribution on thumbnail."""
    accent = get_rgb(style["accent"])
    footer_font = load_font("body", 18)
    draw.text(
        (60, THUMBNAIL_SIZE[1] - 50),
        "Stuart Corrigan  |  Descartes Consulting",
        font=footer_font,
        fill=accent,
    )
