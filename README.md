# SpeakBetter Local

Offline desktop application for structured speaking practice and objective fluency analysis.

No paid APIs. No cloud dependencies. Your speech stays on your machine.

---

## Prerequisites

- **Python 3.10+** installed and available in PATH
- **FFmpeg** installed and available in PATH

---

## Setup (One-Time)

1. Open a terminal in this project folder.

2. Install Python dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create a desktop shortcut (so you can launch with a double-click):
   ```
   python create_shortcut.py
   ```
   This will place a **"SpeakBetter Local"** shortcut on your Windows Desktop.

---

## Usage

- **Double-click** the "SpeakBetter Local" icon on your Desktop.
- The app window opens automatically. No terminal needed.
- On first run, the whisper `base` model (~150 MB) will be downloaded automatically.

---

## Features

- **Random topic generation** from 100+ topics across 5 categories
- **Audio recording** (30–120 seconds) with live timer
- **Local transcription** via faster-whisper (preserves fillers like "uh", "um")
- **Objective metrics**: WPM, filler density, repetition count, pause analysis, sentence stats
- **Visual transcript** with highlighted fillers and repetitions
- **Copy transcript** to clipboard (paste into any external LLM if desired)
- **Session history** stored locally in the browser

---

## Project Structure

```
speech-to-text/
├── backend/
│   ├── config.py          # Centralized configuration
│   ├── topics.py          # 100+ speaking topics
│   ├── transcription.py   # faster-whisper integration
│   ├── metrics.py         # Deterministic metric computation
│   └── main.py            # FastAPI server
├── frontend/
│   ├── index.html         # Dashboard UI
│   ├── css/styles.css     # Design system
│   └── js/app.js          # Frontend logic
├── desktop.py             # Desktop launcher (PyWebView)
├── create_shortcut.py     # One-time shortcut creator
└── requirements.txt       # Python dependencies
```
