"""
Bug2GIF - Streamlit Web Interface

Run locally with:
    streamlit run app.py

Lets you upload screenshots, set speed/size, add step numbers/captions/title,
preview the result, and download a GIF or MP4.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
from typing import List, Optional, Tuple

import streamlit as st
from PIL import Image

# Make the "src" package importable when run via `streamlit run app.py`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gif_generator import (  # noqa: E402
    FrameOptions,
    GifOptions,
    build_frames,
    save_gif,
    save_mp4,
)

st.set_page_config(page_title="Bug2GIF", page_icon="🐞", layout="centered")


def sort_uploaded(files) -> list:
    """Sort uploaded files by name so numeric prefixes stay in order."""
    return sorted(files, key=lambda f: f.name.lower())


def open_uploaded(files) -> List[Image.Image]:
    images = []
    for file in files:
        images.append(Image.open(io.BytesIO(file.getvalue())).convert("RGB"))
    return images


def main() -> None:
    st.title("Bug2GIF")
    st.caption("Turn step-by-step screenshots into one clear animated GIF or MP4.")

    uploaded = st.file_uploader(
        "Upload screenshots (they are ordered by file name)",
        type=["png", "jpg", "jpeg", "bmp", "webp"],
        accept_multiple_files=True,
    )

    if not uploaded:
        st.info("Upload two or more screenshots to get started.")
        return

    files = sort_uploaded(uploaded)
    st.write(f"**{len(files)} screenshot(s) loaded:**")
    st.write(", ".join(f.name for f in files))

    with st.sidebar:
        st.header("Settings")
        duration = st.slider("Frame duration (ms)", 200, 3000, 800, step=100)
        loop_forever = st.checkbox("Loop forever", value=True)

        st.subheader("Size")
        do_resize = st.checkbox("Resize all frames", value=False)
        resize: Optional[Tuple[int, int]] = None
        if do_resize:
            col_w, col_h = st.columns(2)
            width = col_w.number_input("Width", min_value=100, max_value=3000, value=1000)
            height = col_h.number_input("Height", min_value=100, max_value=3000, value=700)
            resize = (int(width), int(height))

        st.subheader("QA extras")
        add_steps = st.checkbox("Add step numbers", value=True)
        add_captions = st.checkbox("Add captions", value=False)
        title = st.text_input("Title frame (optional)", value="")

        export_format = st.radio("Export format", ["GIF", "MP4"], horizontal=True)

    captions: List[str] = []
    if add_captions:
        st.subheader("Captions")
        for file in files:
            captions.append(st.text_input(f"Caption for {file.name}", value=""))

    if st.button("Generate", type="primary"):
        with st.spinner("Building your animation..."):
            images = open_uploaded(files)
            gif_opts = GifOptions(
                duration=duration,
                loop=0 if loop_forever else 1,
                resize=resize,
                title=title.strip() or None,
            )
            frame_opts = FrameOptions(
                captions=captions,
                add_step_numbers=add_steps,
            )
            frames = build_frames(images, frame_opts, gif_opts)

            suffix = ".mp4" if export_format == "MP4" else ".gif"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.close()

            if export_format == "MP4":
                save_mp4(frames, tmp.name, gif_opts)
                mime = "video/mp4"
            else:
                save_gif(frames, tmp.name, gif_opts)
                mime = "image/gif"

            with open(tmp.name, "rb") as handle:
                data = handle.read()

        st.success("Done!")
        if export_format == "MP4":
            st.video(data)
        else:
            st.image(data, caption="Preview")

        st.download_button(
            label=f"Download {export_format}",
            data=data,
            file_name=f"bug_reproduction{suffix}",
            mime=mime,
        )


if __name__ == "__main__":
    main()
