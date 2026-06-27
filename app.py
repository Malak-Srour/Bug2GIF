"""
Bug2GIF — Enhanced Streamlit Web Interface

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import base64
import io
import os
import sys
import tempfile
import time
from typing import Dict, List, Optional, Tuple

import streamlit as st
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gif_generator import (  # noqa: E402
    FrameOptions,
    GifOptions,
    build_frames,
    save_gif,
    save_mp4,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bug2GIF",
    page_icon="🐞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hero header */
.app-header {
    background: linear-gradient(135deg, #fef2f2 0%, #fff7ed 60%, #fef2f2 100%);
    border: 1px solid rgba(220, 38, 38, 0.18);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.app-header h1 {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0 0 0.4rem 0;
    background: linear-gradient(90deg, #dc2626 0%, #ea580c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.app-header p {
    margin: 0;
    color: #6b7280;
    font-size: 0.95rem;
    line-height: 1.6;
}

/* Small stat pill */
.stat-badge {
    display: inline-block;
    background: rgba(220, 38, 38, 0.08);
    color: #dc2626;
    border: 1px solid rgba(220, 38, 38, 0.22);
    border-radius: 20px;
    padding: 0.15rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 0.4rem;
    vertical-align: middle;
}

/* Sidebar section dividers */
.section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #9ca3af;
    margin: 1.4rem 0 0.5rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #e5e7eb;
}

/* Filename below thumbnail */
.frame-label {
    font-size: 0.7rem;
    color: #9ca3af;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 0.15rem;
    text-align: center;
}

/* Empty-state "how it works" cards */
.how-step {
    text-align: center;
    padding: 1.4rem 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    background: #f9fafb;
    height: 100%;
}
.how-step .icon { font-size: 2rem; margin-bottom: 0.5rem; }
.how-step h4    { margin: 0.3rem 0 0.4rem; font-size: 0.9rem; color: #111827; }
.how-step p     { margin: 0; font-size: 0.8rem; color: #6b7280; line-height: 1.5; }

/* Download button strip */
.dl-strip { margin-top: 0.8rem; }

/* Remove excess top padding on main block */
.block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar — all settings ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙ Settings")

    # ANIMATION
    st.markdown('<div class="section-title">Animation</div>', unsafe_allow_html=True)
    duration = st.slider(
        "Frame duration (ms)", 100, 5000, 800, step=50,
        help="How long each frame is shown. 800 ms is a good default.",
    )
    loop_forever    = st.checkbox("Loop forever", value=True)
    per_frame_speed = st.checkbox(
        "Custom speed per frame",
        value=False,
        help="Override the duration for individual frames inside the per-frame panel.",
    )

    # SIZE
    st.markdown('<div class="section-title">Size</div>', unsafe_allow_html=True)
    do_resize = st.checkbox("Resize all frames", value=False)
    resize: Optional[Tuple[int, int]] = None
    if do_resize:
        cw, ch = st.columns(2)
        rw = cw.number_input("Width",  100, 4000, 1280, step=10)
        rh = ch.number_input("Height", 100, 4000,  800, step=10)
        resize = (int(rw), int(rh))

    # OVERLAYS
    st.markdown('<div class="section-title">Overlays</div>', unsafe_allow_html=True)
    add_steps = st.checkbox("Step number badges", value=True)
    if add_steps:
        badge_color = st.color_picker("Badge & highlight colour", "#DC2626")
    else:
        badge_color = "#DC2626"
    show_counter = st.checkbox(
        "Frame counter  (e.g. 2 / 5)",
        value=False,
        help="Draws a small counter in the top-right corner of every frame.",
    )
    title_text = st.text_input(
        "Title frame",
        value="",
        placeholder="Bug: login fails on mobile…",
        help="Adds a title slide at the very start of the animation.",
    )

    # EXPORT
    st.markdown('<div class="section-title">Export format</div>', unsafe_allow_html=True)
    export_fmt = st.radio(
        "Format",
        ["GIF", "MP4", "Both"],
        horizontal=True,
        label_visibility="collapsed",
    )


# ── Hero header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🐞 Bug2GIF</h1>
  <p>
    Turn step-by-step bug screenshots into one clean animated GIF or MP4 —
    perfect for Jira tickets, GitHub issues, Slack messages, and QA reports.
  </p>
</div>
""", unsafe_allow_html=True)


# ── Upload ─────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drop your screenshots here, or click to browse",
    type=["png", "jpg", "jpeg", "bmp", "webp"],
    accept_multiple_files=True,
)

if not uploaded:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown("""
<div class="how-step">
  <div class="icon">📁</div>
  <h4>1 · Upload</h4>
  <p>Drop your bug-reproduction screenshots here.
     They are sorted by file name automatically,
     so name them <code>01_</code>, <code>02_</code>, … to control the order.</p>
</div>""", unsafe_allow_html=True)
    c2.markdown("""
<div class="how-step">
  <div class="icon">⚙️</div>
  <h4>2 · Configure</h4>
  <p>Set frame speed, add step badges, highlight boxes, captions,
     and an optional title slide — all from the sidebar and the per-frame panel.</p>
</div>""", unsafe_allow_html=True)
    c3.markdown("""
<div class="how-step">
  <div class="icon">⬇️</div>
  <h4>3 · Download</h4>
  <p>Hit <strong>Generate</strong> and download your animation as a GIF or MP4 —
     ready to paste anywhere.</p>
</div>""", unsafe_allow_html=True)
    st.stop()


# ── Sort files ─────────────────────────────────────────────────────────────────
files = sorted(uploaded, key=lambda f: f.name.lower())
n_total = len(files)


# ── Frame grid ─────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="margin: 0.8rem 0 0.6rem 0;">'
    f'<span class="stat-badge">{n_total} frame{"s" if n_total != 1 else ""} loaded</span>'
    f'<span style="opacity:0.4; font-size:0.8rem;">Uncheck any frame to skip it.</span>'
    f'</div>',
    unsafe_allow_html=True,
)

COLS_PER_ROW = 6
include_flags: Dict[str, bool] = {}

rows = [files[i : i + COLS_PER_ROW] for i in range(0, n_total, COLS_PER_ROW)]
for row in rows:
    cols = st.columns(len(row))
    for file, col in zip(row, cols):
        with col:
            thumb = Image.open(io.BytesIO(file.getvalue()))
            st.image(thumb, use_container_width=True)
            include_flags[file.name] = st.checkbox(
                "Include", value=True, key=f"inc_{file.name}"
            )
            st.markdown(
                f'<div class="frame-label">{file.name}</div>',
                unsafe_allow_html=True,
            )

active_files = [f for f in files if include_flags.get(f.name, True)]

if not active_files:
    st.warning("All frames are excluded — enable at least one frame to continue.")
    st.stop()

n_active = len(active_files)
if n_active < n_total:
    st.markdown(
        f'<span class="stat-badge">{n_active} / {n_total} frames active</span>',
        unsafe_allow_html=True,
    )


# ── Per-frame settings ─────────────────────────────────────────────────────────
captions: List[str] = []
highlights: List[Optional[Tuple[int, int, int, int]]] = []
per_frame_durations: List[int] = []

expander_label = (
    f"Per-frame settings — captions · highlights"
    + (" · speed" if per_frame_speed else "")
    + f"  ({n_active} frame{'s' if n_active != 1 else ''})"
)

with st.expander(expander_label, expanded=False):
    # Column header row
    if per_frame_speed:
        hcols = st.columns([0.4, 3.5, 1.4, 3.7])
        hcols[0].markdown("**#**")
        hcols[1].markdown("**Caption**")
        hcols[2].markdown("**ms**")
        hcols[3].markdown("**Highlight box** — enable then enter x1 y1 x2 y2")
    else:
        hcols = st.columns([0.4, 4.5, 4.1])
        hcols[0].markdown("**#**")
        hcols[1].markdown("**Caption**")
        hcols[2].markdown("**Highlight box** — enable then enter x1 y1 x2 y2")

    st.markdown(
        '<hr style="margin: 0.4rem 0 0.8rem; opacity: 0.12;">',
        unsafe_allow_html=True,
    )

    for i, file in enumerate(active_files):
        if per_frame_speed:
            c_n, c_cap, c_dur, c_hl = st.columns([0.4, 3.5, 1.4, 3.7])
        else:
            c_n, c_cap, c_hl = st.columns([0.4, 4.5, 4.1])

        c_n.markdown(f"**{i + 1}**")

        with c_cap:
            cap = st.text_input(
                "caption",
                key=f"cap_{file.name}",
                label_visibility="collapsed",
                placeholder=f"Caption for frame {i + 1}…",
            )
            captions.append(cap)

        if per_frame_speed:
            with c_dur:
                fd = st.number_input(
                    "ms",
                    min_value=100,
                    max_value=10000,
                    value=duration,
                    step=50,
                    key=f"dur_{file.name}",
                    label_visibility="collapsed",
                )
                per_frame_durations.append(int(fd))

        with c_hl:
            add_hl = st.checkbox("Add highlight", key=f"hl_en_{file.name}")
            if add_hl:
                hc = st.columns(4)
                x1 = hc[0].number_input("x1", 0, 9999, 0,   step=1, key=f"x1_{file.name}", label_visibility="collapsed")
                y1 = hc[1].number_input("y1", 0, 9999, 0,   step=1, key=f"y1_{file.name}", label_visibility="collapsed")
                x2 = hc[2].number_input("x2", 0, 9999, 200, step=1, key=f"x2_{file.name}", label_visibility="collapsed")
                y2 = hc[3].number_input("y2", 0, 9999, 200, step=1, key=f"y2_{file.name}", label_visibility="collapsed")
                highlights.append((int(x1), int(y1), int(x2), int(y2)))
            else:
                highlights.append(None)


# ── Generate button ────────────────────────────────────────────────────────────
st.markdown("---")
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    generate = st.button(
        "Generate Animation",
        type="primary",
        use_container_width=True,
    )

# Initialise result store
if "results" not in st.session_state:
    st.session_state.results = {}

if generate:
    # Convert hex badge colour → RGB tuple
    hx = badge_color.lstrip("#")
    badge_rgb: Tuple[int, int, int] = tuple(int(hx[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[assignment]

    gif_opts = GifOptions(
        duration=duration,
        loop=0 if loop_forever else 1,
        resize=resize,
        title=title_text.strip() or None,
        durations=per_frame_durations if per_frame_speed else None,
    )
    frame_opts = FrameOptions(
        captions=captions,
        highlights=highlights,
        add_step_numbers=add_steps,
        step_color=badge_rgb,
        show_frame_counter=show_counter,
    )

    bar = st.progress(0, text="Loading images…")
    images = [Image.open(io.BytesIO(f.getvalue())).convert("RGB") for f in active_files]

    bar.progress(20, text="Applying overlays…")
    frames = build_frames(images, frame_opts, gif_opts)

    bar.progress(55, text="Encoding output…")
    output_data: Dict[str, bytes] = {}

    if export_fmt in ("GIF", "Both"):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".gif")
        tmp.close()
        save_gif(frames, tmp.name, gif_opts)
        with open(tmp.name, "rb") as fh:
            output_data["gif"] = fh.read()

    if export_fmt in ("MP4", "Both"):
        bar.progress(75, text="Encoding MP4…")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp.close()
        save_mp4(frames, tmp.name, gif_opts)
        with open(tmp.name, "rb") as fh:
            output_data["mp4"] = fh.read()

    bar.progress(100, text="Done!")
    bar.empty()

    st.session_state.results = {
        "data":     output_data,
        "n_frames": len(frames),
        "fmt":      export_fmt,
        "gen_id":   int(time.time() * 1000),  # unique key per generation
    }


# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.get("results"):
    res      = st.session_state.results
    data     = res["data"]
    n_frames = res["n_frames"]

    st.success(f"Animation ready — {n_frames} frame{'s' if n_frames != 1 else ''} generated.")

    # ── Preview ────────────────────────────────────────────────────────────────
    if "gif" in data:
        # Embed via data URI so the browser handles the animation natively.
        # st.image() decodes through PIL and only shows the first frame.
        b64 = base64.b64encode(data["gif"]).decode()
        st.markdown(
            f'<img src="data:image/gif;base64,{b64}" '
            f'style="max-width:100%; border-radius:10px; display:block; margin:0 auto;">',
            unsafe_allow_html=True,
        )
        st.caption("Animated GIF preview")

    if "mp4" in data:
        label = "MP4 preview" if "gif" in data else None
        if label:
            with st.expander("MP4 preview", expanded=False):
                st.video(data["mp4"])
        else:
            st.video(data["mp4"])

    # ── Download buttons ───────────────────────────────────────────────────────
    # key includes gen_id so Streamlit treats buttons as new widgets after each
    # generation — prevents the positional-key re-fire on the post-click re-run.
    gen_id = res.get("gen_id", 0)
    dl_cols = st.columns(len(data))
    for col, (ext, raw) in zip(dl_cols, data.items()):
        mime = "image/gif" if ext == "gif" else "video/mp4"
        with col:
            st.download_button(
                label=f"⬇  Download {ext.upper()}",
                data=raw,
                file_name=f"bug_reproduction.{ext}",
                mime=mime,
                use_container_width=True,
                key=f"dl_{ext}_{gen_id}",
            )

    # File size info
    size_badges = " ".join(
        f'<span class="stat-badge">{ext.upper()} · {len(raw) / 1024:.0f} KB</span>'
        for ext, raw in data.items()
    )
    st.markdown(
        f'<div style="margin-top: 0.6rem;">{size_badges}</div>',
        unsafe_allow_html=True,
    )
