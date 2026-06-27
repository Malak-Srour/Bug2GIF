# Bug2GIF — QA Screenshot GIF Generator

Convert step-by-step screenshots into one clean animated **GIF** (or **MP4**) to make
bug reports clearer in GitHub issues, Jira, Trello, and QA documentation.

Instead of attaching ten separate screenshots, you put them in a folder, run one
command (or use the web app), and get a single animation that shows the bug flow
from start to finish.

## Features

- Folder of screenshots → one GIF, ordered automatically by file name
- Custom frame duration and loop control
- Resizes mismatched screenshots to a consistent size (no stretching)
- QA extras: **step numbers**, **captions**, **title frame**, **highlight boxes**
- **MP4 export** in addition to GIF
- **Command line tool** (`main.py`) and a **Streamlit web app** (`app.py`)

## Project structure

```
bug2gif/
├── README.md
├── requirements.txt
├── main.py            # command line interface
├── app.py             # Streamlit web interface
├── input/screenshots/ # put your screenshots here
├── output/            # generated GIFs / MP4s
├── examples/          # sample captions file
└── src/
    ├── gif_generator.py
    ├── image_utils.py
    └── caption_utils.py
```

---

## Setup on Windows 11 (your ThinkPad X1 Yoga)

You'll use **Windows PowerShell** (open Start → type "PowerShell" → Enter).

### 1. Install Python

If you don't have Python yet, install **Python 3.11 or 3.12** from
[python.org/downloads](https://www.python.org/downloads/).
During install, check the box **"Add python.exe to PATH"**.

Verify it works:

```powershell
python --version
```

### 2. Go to the project folder

```powershell
cd path\to\bug2gif
```

(For example `cd C:\Users\YourName\Downloads\bug2gif`.)

### 3. Create and activate a virtual environment (recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the activate script, run this once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 4. Install the dependencies

```powershell
pip install -r requirements.txt
```

> The MP4 export uses `imageio-ffmpeg`, which downloads ffmpeg automatically on
> first use — no separate install needed.

---

## Usage — Command Line

1. Put your screenshots in `input\screenshots\`, named in order:

   ```
   01_open_page.png
   02_click_submit.png
   03_error_appears.png
   ```

2. Run the tool:

   ```powershell
   python main.py --input input\screenshots --output output\bug.gif
   ```

3. Open `output\bug.gif`.

### Options

| Option | Description | Example |
| --- | --- | --- |
| `--input`, `-i` | Folder of screenshots (required) | `input\screenshots` |
| `--output`, `-o` | Output file (.gif or .mp4) | `output\bug.gif` |
| `--duration`, `-d` | Milliseconds per frame | `800` |
| `--loop`, `-l` | `0` = loop forever, `1` = play once | `0` |
| `--resize`, `-r` | Resize all frames `WIDTHxHEIGHT` | `1000x700` |
| `--steps` | Add "Step 1", "Step 2" badges | |
| `--title` | Add a title frame at the start | `"Bug: save fails"` |
| `--captions` | Text file, one caption per line | `examples\captions.txt` |
| `--mp4` | Export MP4 instead of GIF | |

### Full example

```powershell
python main.py `
  --input input\screenshots `
  --output output\bug.gif `
  --duration 800 `
  --loop 0 `
  --resize 1000x700 `
  --steps `
  --title "Bug: Validation message stays visible after save" `
  --captions examples\captions.txt
```

Export an MP4 instead:

```powershell
python main.py --input input\screenshots --output output\bug.mp4 --mp4 --steps
```

---

## Usage — Web App (Streamlit)

```powershell
streamlit run app.py
```

Your browser opens at `http://localhost:8501`. There you can upload screenshots,
set speed and size, add step numbers/captions/title, preview the result, and
download a GIF or MP4.

---

## Notes

- Captions in the `--captions` file are matched to screenshots **in order**
  (line 1 → first screenshot, etc.).
- Supported input types: PNG, JPG/JPEG, BMP, WEBP, GIF.
- If a font isn't found for text overlays, the tool falls back to a built-in
  font so it never crashes.

## Skills demonstrated

Python, image processing (Pillow), file handling, CLI design (argparse),
a Streamlit web UI, and QA-focused bug documentation.
