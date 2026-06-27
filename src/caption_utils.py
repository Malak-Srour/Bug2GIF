"""
caption_utils.py
----------------
Functions for drawing QA-friendly annotations on screenshots:

- Step numbers (Step 1, Step 2, ...)
- Captions (a short line of text per screenshot)
- Highlight boxes (a rectangle around an important area)
- A title frame (a plain frame shown at the start of the GIF)

All drawing is done with Pillow's ImageDraw module.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Colors used throughout (R, G, B).
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)
ACCENT = (220, 38, 38)  # a clear red for highlights / "bug" emphasis
BAR = (17, 17, 17)      # caption bar background


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Try to load a common TrueType font. Falls back to Pillow's default
    bitmap font if no system font is found (so the tool never crashes).
    """
    candidates = [
        "arial.ttf",            # Windows
        "DejaVuSans.ttf",       # Linux / Pillow bundled
        "DejaVuSans-Bold.ttf",
        "Helvetica.ttf",        # macOS-ish
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    # Last resort: built-in font (size is fixed, but it works everywhere).
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> Tuple[int, int]:
    """Measure rendered text size in a way that works across Pillow versions."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def add_step_number(image: Image.Image, step: int) -> Image.Image:
    """Draw a 'Step N' badge in the top-left corner of the image."""
    img = image.copy()
    draw = ImageDraw.Draw(img)

    font_size = max(18, img.width // 28)
    font = _load_font(font_size)
    text = f"Step {step}"

    text_w, text_h = _text_size(draw, text, font)
    pad = font_size // 2

    # Rounded-ish badge background.
    box = [10, 10, 10 + text_w + pad * 2, 10 + text_h + pad * 2]
    draw.rectangle(box, fill=ACCENT)
    draw.text((10 + pad, 10 + pad), text, fill=WHITE, font=font)
    return img


def add_caption(image: Image.Image, caption: str) -> Image.Image:
    """
    Draw a caption inside a solid bar at the bottom of the image.
    Long captions are wrapped onto multiple lines.
    """
    if not caption:
        return image

    img = image.copy()
    draw = ImageDraw.Draw(img)

    font_size = max(16, img.width // 36)
    font = _load_font(font_size)

    # Wrap text to fit the image width.
    max_text_width = img.width - 40
    lines = _wrap_text(draw, caption, font, max_text_width)

    line_h = _text_size(draw, "Ag", font)[1] + 6
    bar_h = line_h * len(lines) + 20
    bar_top = img.height - bar_h

    # Semi-transparent looking dark bar (solid here for simplicity).
    draw.rectangle([0, bar_top, img.width, img.height], fill=BAR)

    y = bar_top + 10
    for line in lines:
        draw.text((20, y), line, fill=WHITE, font=font)
        y += line_h

    return img


def add_highlight_box(
    image: Image.Image,
    box: Tuple[int, int, int, int],
    width: int = 4,
) -> Image.Image:
    """
    Draw a rectangle (x1, y1, x2, y2) to highlight an important area.
    Coordinates are in pixels relative to the image.
    """
    img = image.copy()
    draw = ImageDraw.Draw(img)
    draw.rectangle(list(box), outline=ACCENT, width=width)
    return img


def make_title_frame(
    title: str,
    size: Tuple[int, int],
    background: Tuple[int, int, int] = WHITE,
) -> Image.Image:
    """
    Create a standalone title frame, e.g.
    'Bug: Validation message stays visible after save'.
    The text is centered and wrapped to fit the frame.
    """
    frame = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(frame)

    font_size = max(22, size[0] // 22)
    font = _load_font(font_size)

    max_text_width = size[0] - 80
    lines = _wrap_text(draw, title, font, max_text_width)

    line_h = _text_size(draw, "Ag", font)[1] + 12
    total_h = line_h * len(lines)
    y = (size[1] - total_h) // 2

    for line in lines:
        line_w = _text_size(draw, line, font)[0]
        x = (size[0] - line_w) // 2
        draw.text((x, y), line, fill=BLACK, font=font)
        y += line_h

    return frame


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    max_width: int,
) -> List[str]:
    """Break ``text`` into lines that each fit within ``max_width`` pixels."""
    words = text.split()
    if not words:
        return [""]

    lines: List[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def annotate_frame(
    image: Image.Image,
    step: Optional[int] = None,
    caption: Optional[str] = None,
    highlight: Optional[Tuple[int, int, int, int]] = None,
) -> Image.Image:
    """
    Apply the requested annotations to a single frame in a sensible order:
    highlight box first, then step badge, then caption bar.
    """
    result = image
    if highlight is not None:
        result = add_highlight_box(result, highlight)
    if step is not None:
        result = add_step_number(result, step)
    if caption:
        result = add_caption(result, caption)
    return result
