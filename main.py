"""
Bug2GIF - QA Screenshot GIF Generator (Command Line Interface)

Convert a folder of step-by-step screenshots into one animated GIF (or MP4).

Basic example:
    python main.py --input input/screenshots --output output/bug.gif

Full example:
    python main.py \
        --input input/screenshots \
        --output output/bug.gif \
        --duration 800 \
        --loop 0 \
        --resize 1000x700 \
        --steps \
        --title "Bug: Validation message stays visible after save" \
        --captions captions.txt
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Tuple

# Allow running this file directly (python main.py) by making "src" importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gif_generator import (  # noqa: E402
    FrameOptions,
    GifOptions,
    generate_from_folder,
)


def parse_resize(value: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse a 'WIDTHxHEIGHT' string like '1000x700' into a tuple."""
    if not value:
        return None
    try:
        width, height = value.lower().split("x")
        return (int(width), int(height))
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid --resize value '{value}'. Use the form WIDTHxHEIGHT, e.g. 1000x700."
        )


def load_captions(path: Optional[str]) -> List[str]:
    """Read captions from a text file, one caption per line."""
    if not path:
        return []
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Captions file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bug2gif",
        description="Convert step-by-step screenshots into an animated GIF or MP4.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Folder containing screenshots (sorted by file name).",
    )
    parser.add_argument(
        "--output", "-o", default="output/bug_reproduction.gif",
        help="Output file path (.gif or .mp4).",
    )
    parser.add_argument(
        "--duration", "-d", type=int, default=800,
        help="How long each frame is shown, in milliseconds.",
    )
    parser.add_argument(
        "--loop", "-l", type=int, default=0,
        help="GIF loop count. 0 = loop forever, 1 = play once.",
    )
    parser.add_argument(
        "--resize", "-r", type=parse_resize, default=None,
        help="Resize all frames to WIDTHxHEIGHT (e.g. 1000x700).",
    )
    parser.add_argument(
        "--steps", action="store_true",
        help="Add 'Step 1', 'Step 2', ... badges to each frame.",
    )
    parser.add_argument(
        "--title", default=None,
        help="Add a title frame at the start of the GIF.",
    )
    parser.add_argument(
        "--captions", default=None,
        help="Path to a text file with one caption per line (matches frame order).",
    )
    parser.add_argument(
        "--mp4", action="store_true",
        help="Export as MP4 video instead of GIF (output should end with .mp4).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    captions = load_captions(args.captions)

    gif_opts = GifOptions(
        duration=args.duration,
        loop=args.loop,
        resize=args.resize,
        title=args.title,
    )
    frame_opts = FrameOptions(
        captions=captions,
        add_step_numbers=args.steps,
    )

    as_mp4 = args.mp4 or args.output.lower().endswith(".mp4")

    try:
        output = generate_from_folder(
            input_folder=args.input,
            output_path=args.output,
            gif_opts=gif_opts,
            frame_opts=frame_opts,
            as_mp4=as_mp4,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    kind = "MP4" if as_mp4 else "GIF"
    print(f"Done! {kind} saved to: {os.path.abspath(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
