"""
image_utils.py
--------------
Helpers for loading, ordering, and resizing screenshots before they are
turned into a GIF or MP4.

These functions intentionally only depend on Pillow (PIL) so they are easy
to read and reuse.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from PIL import Image

# File extensions we treat as valid screenshots.
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")


def list_image_files(folder: str) -> List[str]:
    """
    Return a sorted list of image file paths found inside ``folder``.

    Sorting is done by file name so screenshots named like
    ``01_open.png``, ``02_click.png``, ``03_error.png`` come out in the
    correct order automatically.
    """
    if not os.path.isdir(folder):
        raise NotADirectoryError(f"Input folder does not exist: {folder}")

    files = [
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if name.lower().endswith(SUPPORTED_EXTENSIONS)
    ]

    # Case-insensitive sort by file name keeps numeric prefixes in order.
    files.sort(key=lambda path: os.path.basename(path).lower())

    if not files:
        raise FileNotFoundError(
            f"No supported image files found in: {folder}\n"
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    return files


def load_images(paths: List[str]) -> List[Image.Image]:
    """Open a list of image paths and return them as RGB Pillow images."""
    images: List[Image.Image] = []
    for path in paths:
        with Image.open(path) as img:
            # Convert to RGB so JPGs, PNGs with alpha, etc. all behave the same.
            images.append(img.convert("RGB"))
    return images


def get_target_size(
    images: List[Image.Image],
    resize: Optional[Tuple[int, int]] = None,
) -> Tuple[int, int]:
    """
    Decide on a single (width, height) that every frame will share.

    If ``resize`` is provided, that exact size is used. Otherwise we use the
    size of the widest/tallest image so nothing gets cropped.
    """
    if resize is not None:
        return resize

    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)
    return (max_width, max_height)


def fit_to_canvas(
    image: Image.Image,
    size: Tuple[int, int],
    background: Tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """
    Resize ``image`` to fit inside ``size`` while keeping its aspect ratio,
    then center it on a solid background canvas of exactly ``size``.

    This avoids stretching screenshots that have different dimensions.
    """
    target_w, target_h = size
    img = image.copy()

    # Scale down/up while preserving aspect ratio.
    img.thumbnail((target_w, target_h), Image.LANCZOS)

    canvas = Image.new("RGB", size, background)
    offset_x = (target_w - img.width) // 2
    offset_y = (target_h - img.height) // 2
    canvas.paste(img, (offset_x, offset_y))
    return canvas


def normalize_images(
    images: List[Image.Image],
    resize: Optional[Tuple[int, int]] = None,
    background: Tuple[int, int, int] = (255, 255, 255),
) -> List[Image.Image]:
    """
    Make every image the same size so the final GIF/MP4 looks consistent.

    Returns a new list of images; the originals are not modified.
    """
    size = get_target_size(images, resize)
    return [fit_to_canvas(img, size, background) for img in images]
