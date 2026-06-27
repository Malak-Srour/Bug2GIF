"""
caption_utils.py
----------------
Functions for drawing QA-friendly annotations on screenshots:

- Step number badges  (Step 1, Step 2, …)
- Frame counter       (e.g. 2 / 5) in the top-right corner
- Captions            (a wrapped text bar at the bottom)
- Highlight boxes     (a coloured rectangle around an important area)
- Title frame         (a plain frame shown at the start of the GIF)

All drawing is done with Pillow's ImageDraw module.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Default palette
WHITE  = (255, 255, 255)
BLACK  = (17,  17,  17)
ACCENT = (220, 38,  38)   # red — badges, highlights
BAR    = (17,  17,  17)   # caption bar background


# ── Font helpers ───────────────────────────────────────────────────────────────

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Try common TrueType fonts; fall back to Pillow's built-in bitmap font
    so the tool never crashes on systems without TTF fonts installed.
    """
    candidates = [
        "arial.ttf",
        "arialbd.ttf",
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "Helvetica.ttf",
        "LiberationSans-Regular.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> Tuple[int, int]:
    """Return (width, height) of ``text`` rendered with ``font``."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


# ── Individual annotation functions ───────────────────────────────────────────

def add_step_number(
    image: Image.Image,
    step: int,
    color: Tuple[int, int, int] = ACCENT,
) -> Image.Image:
    """Draw a 'Step N' badge in the top-left corner of the image."""
    img  = image.copy()
    draw = ImageDraw.Draw(img)

    font_size = max(18, img.width // 28)
    font = _load_font(font_size)
    text = f"Step {step}"

    text_w, text_h = _text_size(draw, text, font)
    pad = font_size // 2

    box = [10, 10, 10 + text_w + pad * 2, 10 + text_h + pad * 2]
    draw.rectangle(box, fill=color)
    draw.text((10 + pad, 10 + pad), text, fill=WHITE, font=font)
    return img


def add_frame_counter(
    image: Image.Image,
    current: int,
    total: int,
    color: Tuple[int, int, int] = (40, 40, 40),
) -> Image.Image:
    """Draw an 'X / Y' counter in the top-right corner."""
    img  = image.copy()
    draw = ImageDraw.Draw(img)

    font_size = max(14, img.width // 40)
    font = _load_font(font_size)
    text = f"{current} / {total}"

    text_w, text_h = _text_size(draw, text, font)
    pad    = font_size // 2
    margin = 10

    x   = img.width - text_w - pad * 2 - margin
    box = [x, margin, img.width - margin, margin + text_h + pad * 2]
    draw.rectangle(box, fill=color)
    draw.text((x + pad, margin + pad), text, fill=WHITE, font=font)
    return img


def add_caption(image: Image.Image, caption: str) -> Image.Image:
    """Draw a caption inside a solid bar at the bottom of the image."""
    if not caption:
        return image

    img  = image.copy()
    draw = ImageDraw.Draw(img)

    font_size = max(16, img.width // 36)
    font = _load_font(font_size)

    max_text_width = img.width - 40
    lines = _wrap_text(draw, caption, font, max_text_width)

    line_h = _text_size(draw, "Ag", font)[1] + 6
    bar_h  = line_h * len(lines) + 20
    bar_top = img.height - bar_h

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
    color: Tuple[int, int, int] = ACCENT,
) -> Image.Image:
    """Draw a rectangle (x1, y1, x2, y2) to highlight an important area."""
    img  = image.copy()
    draw = ImageDraw.Draw(img)
    draw.rectangle(list(box), outline=color, width=width)
    return img


def make_title_frame(
    title: str,
    size: Tuple[int, int],
    background: Tuple[int, int, int] = WHITE,
    text_color: Tuple[int, int, int] = BLACK,
    accent_color: Tuple[int, int, int] = ACCENT,
) -> Image.Image:
    """
    Create a standalone title frame with centred, wrapped text and a thin
    accent underline drawn below the last line.
    """
    frame = Image.new("RGB", size, background)
    draw  = ImageDraw.Draw(frame)

    font_size = max(22, size[0] // 22)
    font = _load_font(font_size)

    max_text_width = size[0] - 80
    lines = _wrap_text(draw, title, font, max_text_width)

    line_h  = _text_size(draw, "Ag", font)[1] + 12
    total_h = line_h * len(lines)
    y = (size[1] - total_h) // 2

    widths = []
    for line in lines:
        line_w = _text_size(draw, line, font)[0]
        widths.append(line_w)
        x = (size[0] - line_w) // 2
        draw.text((x, y), line, fill=text_color, font=font)
        y += line_h

    # Thin accent underline below the last text line
    max_w  = max(widths) if widths else 60
    bar_x  = (size[0] - max_w) // 2
    bar_y  = y + 6
    bar_h  = max(4, font_size // 8)
    draw.rectangle([bar_x, bar_y, bar_x + max_w, bar_y + bar_h], fill=accent_color)

    return frame


# ── Combined annotation ────────────────────────────────────────────────────────

def annotate_frame(
    image: Image.Image,
    step: Optional[int] = None,
    caption: Optional[str] = None,
    highlight: Optional[Tuple[int, int, int, int]] = None,
    step_color: Tuple[int, int, int] = ACCENT,
    frame_counter: Optional[Tuple[int, int]] = None,
) -> Image.Image:
    """
    Apply all requested annotations to one frame in a sensible order:
    highlight box first (drawn under text), then step badge, then frame
    counter, then caption bar.
    """
    result = image
    if highlight is not None:
        result = add_highlight_box(result, highlight, color=step_color)
    if step is not None:
        result = add_step_number(result, step, color=step_color)
    if frame_counter is not None:
        result = add_frame_counter(result, frame_counter[0], frame_counter[1])
    if caption:
        result = add_caption(result, caption)
    return result


# ── Internal helpers ───────────────────────────────────────────────────────────

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
