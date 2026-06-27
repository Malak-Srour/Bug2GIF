# Bug2GIF — QA Screenshot GIF Generator

Convert step-by-step screenshots into one clean animated **GIF** (or **MP4**) to make
bug reports clearer in GitHub issues, Jira, Trello, and QA documentation.

Instead of attaching ten separate screenshots, upload them to the web app (or drop
them in a folder and run one command), and get a single animation that shows the bug
flow from start to finish.

---

## Features

- Folder of screenshots → one GIF or MP4, ordered automatically by file name
- Custom frame duration and loop control
- **Per-frame duration** — set a different speed for each individual frame
- Resizes mismatched screenshots to a consistent size (no stretching)
- QA extras: **step number badges**, **captions**, **title frame**, **highlight boxes**
- **Custom badge & highlight colour** — pick any colour via a colour picker
- **Frame counter overlay** — draws "2 / 5" in the top-right corner of every frame
- **MP4 export** in addition to GIF, or **export both at once**
- **Command line tool** (`main.py`) and a **Streamlit web app** (`app.py`)

---

## Project structure

```
bug2gif/
├── README.md
├── requirements.txt
├── main.py                 # command line interface
├── app.py                  # Streamlit web interface
├── .streamlit/
│   └── config.toml         # Streamlit theme (light mode, red accent)
├── input/screenshots/      # put your screenshots here (CLI mode)
├── output/                 # generated GIFs / MP4s
├── examples/               # sample captions file
└── src/
    ├── gif_generator.py
    ├── image_utils.py
    └── caption_utils.py
```

---

## Setup

### 1. Install Python

Install **Python 3.10 or newer** from [python.org/downloads](https://www.python.org/downloads/).
During install, check **"Add python.exe to PATH"**.

Verify:

```powershell
python --version
```

### 2. Create a virtual environment

```powershell
cd path\to\bug2gif
python -m venv .venv
```

### 3. Install dependencies

```powershell
.venv\Scripts\pip install -r requirements.txt
```

> MP4 export uses `imageio-ffmpeg`, which downloads ffmpeg automatically on first
> use — no separate install needed.

---

## Usage — Web App (recommended)

```powershell
.venv\Scripts\streamlit run app.py
```

Your browser opens at `http://localhost:8501`.

### Workflow

1. **Upload** your screenshots — they are sorted by file name automatically.
   Name them `01_`, `02_`, … to control the order.
2. **Exclude frames** — uncheck the thumbnail of any frame you want to skip.
3. **Configure** in the sidebar:
   | Setting | Description |
   |---|---|
   | Frame duration | How long each frame is shown (ms) |
   | Loop forever | Whether the GIF repeats |
   | Custom speed per frame | Override duration per frame in the per-frame panel |
   | Resize all frames | Scale every frame to a fixed width × height |
   | Step number badges | Draw "Step 1", "Step 2", … on each frame |
   | Badge & highlight colour | Pick any colour for badges and highlight boxes |
   | Frame counter | Draw "2 / 5" in the top-right corner |
   | Title frame | Add a title slide at the very start |
   | Export format | GIF, MP4, or both at once |

4. Open **Per-frame settings** to set captions, highlight boxes (x1 y1 x2 y2),
   and per-frame duration for each individual frame.
5. Click **Generate Animation**.
6. Preview the animated GIF inline, then download GIF and/or MP4.

---

## Usage — Command Line

1. Put your screenshots in `input\screenshots\`, named in order:

   ```
   01_open_page.png
   02_click_submit.png
   03_error_appears.png
   ```

2. Run:

   ```powershell
   .venv\Scripts\python main.py --input input\screenshots --output output\bug.gif
   ```

3. Open `output\bug.gif`.

### Options

| Option | Description | Default |
|---|---|---|
| `--input`, `-i` | Folder of screenshots (required) | — |
| `--output`, `-o` | Output file path (`.gif` or `.mp4`) | `output/bug_reproduction.gif` |
| `--duration`, `-d` | Milliseconds per frame | `800` |
| `--loop`, `-l` | `0` = loop forever, `1` = play once | `0` |
| `--resize`, `-r` | Resize all frames `WIDTHxHEIGHT` | — |
| `--steps` | Add "Step N" badges | off |
| `--title` | Add a title frame at the start | — |
| `--captions` | Text file with one caption per line | — |
| `--mp4` | Export MP4 instead of GIF | off |

### Full example

```powershell
.venv\Scripts\python main.py `
  --input input\screenshots `
  --output output\bug.gif `
  --duration 800 `
  --loop 0 `
  --resize 1000x700 `
  --steps `
  --title "Bug: Validation message stays visible after save" `
  --captions examples\captions.txt
```

Export as MP4:

```powershell
.venv\Scripts\python main.py --input input\screenshots --output output\bug.mp4 --mp4 --steps
```

---

## Notes

- Captions in `--captions` are matched to screenshots **in order** (line 1 → first screenshot).
- Supported input formats: PNG, JPG/JPEG, BMP, WEBP, GIF.
- If no TrueType font is found for overlays, the tool falls back to Pillow's built-in
  font so it never crashes.
- The web app runs on a **light theme** by default (configured in `.streamlit/config.toml`).
