"""
gif_generator.py
----------------
The core engine that turns a list of (annotated) frames into a GIF or MP4.

It ties together image_utils (loading + resizing) and caption_utils
(step numbers, captions, highlight boxes, title frame).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from PIL import Image

from .caption_utils import annotate_frame, make_title_frame
from .image_utils import list_image_files, load_images, normalize_images


@dataclass
class FrameOptions:
    """Per-image annotation options. The lists are parallel to the images."""
    captions: List[str] = field(default_factory=list)
    highlights: List[Optional[Tuple[int, int, int, int]]] = field(default_factory=list)
    add_step_numbers: bool = False


@dataclass
class GifOptions:
    """Global settings for building the GIF / MP4."""
    duration: int = 800          # milliseconds per frame
    loop: int = 0                # 0 = loop forever, 1 = play once
    resize: Optional[Tuple[int, int]] = None
    title: Optional[str] = None  # if set, a title frame is prepended
    fps: Optional[float] = None  # used for MP4; derived from duration if None


def build_frames(
    images: List[Image.Image],
    frame_opts: Optional[FrameOptions] = None,
    gif_opts: Optional[GifOptions] = None,
) -> List[Image.Image]:
    """
    Normalize images to a uniform size, apply annotations, and optionally
    prepend a title frame. Returns the final list of frames.
    """
    frame_opts = frame_opts or FrameOptions()
    gif_opts = gif_opts or GifOptions()

    frames = normalize_images(images, resize=gif_opts.resize)
    size = frames[0].size if frames else (800, 600)

    annotated: List[Image.Image] = []
    for index, frame in enumerate(frames):
        caption = (
            frame_opts.captions[index]
            if index < len(frame_opts.captions)
            else None
        )
        highlight = (
            frame_opts.highlights[index]
            if index < len(frame_opts.highlights)
            else None
        )
        step = index + 1 if frame_opts.add_step_numbers else None
        annotated.append(
            annotate_frame(frame, step=step, caption=caption, highlight=highlight)
        )

    if gif_opts.title:
        annotated.insert(0, make_title_frame(gif_opts.title, size))

    return annotated


def save_gif(frames: List[Image.Image], output_path: str, gif_opts: GifOptions) -> str:
    """Save frames as an animated GIF and return the output path."""
    if not frames:
        raise ValueError("No frames to save.")

    _ensure_parent_dir(output_path)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=gif_opts.duration,
        loop=gif_opts.loop,
        optimize=True,
        disposal=2,
    )
    return output_path


def save_mp4(frames: List[Image.Image], output_path: str, gif_opts: GifOptions) -> str:
    """
    Save frames as an MP4 video using imageio + ffmpeg.
    Imported lazily so GIF-only users don't need imageio installed.
    """
    if not frames:
        raise ValueError("No frames to save.")

    import imageio.v2 as imageio  # lazy import
    import numpy as np

    _ensure_parent_dir(output_path)

    fps = gif_opts.fps or (1000.0 / max(gif_opts.duration, 1))

    # MP4 (H.264) requires even width/height; pad if needed.
    even_frames = [_pad_to_even(f) for f in frames]

    writer = imageio.get_writer(output_path, fps=fps, codec="libx264", quality=8)
    try:
        for frame in even_frames:
            writer.append_data(np.asarray(frame))
    finally:
        writer.close()
    return output_path


def generate_from_folder(
    input_folder: str,
    output_path: str,
    gif_opts: Optional[GifOptions] = None,
    frame_opts: Optional[FrameOptions] = None,
    as_mp4: bool = False,
) -> str:
    """
    High-level helper used by the CLI: read a folder of screenshots and
    produce a GIF (or MP4) at ``output_path``.
    """
    gif_opts = gif_opts or GifOptions()
    paths = list_image_files(input_folder)
    images = load_images(paths)
    frames = build_frames(images, frame_opts, gif_opts)

    if as_mp4:
        return save_mp4(frames, output_path, gif_opts)
    return save_gif(frames, output_path, gif_opts)


def _pad_to_even(image: Image.Image) -> Image.Image:
    """Pad an image so width and height are even numbers (required by H.264)."""
    w, h = image.size
    new_w = w + (w % 2)
    new_h = h + (h % 2)
    if (new_w, new_h) == (w, h):
        return image
    padded = Image.new("RGB", (new_w, new_h), (255, 255, 255))
    padded.paste(image, (0, 0))
    return padded


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
