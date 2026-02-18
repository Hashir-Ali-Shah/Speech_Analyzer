# SpeechLab

Offline desktop application for structured speaking practice and objective fluency analysis.

No paid APIs. No cloud dependencies. Your speech stays on your machine.

---

## Prerequisites

- **Python 3.10+** installed and available in PATH
- **FFmpeg** installed and available in PATH

---

## Setup

### 1. Install Dependencies

```
pip install -r requirements.txt
```

### 2. Download Whisper Models

SpeechLab uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) models for local transcription. You need to download at least the **base** model before running the app.

**Install the download tool:**

```python
pip install huggingface_hub
```

**Download to default cache directory:**

```python
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-base', repo_type='model')"
```

```python
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-medium', repo_type='model')"
```

**Download to a specific directory:**

```python
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-base', repo_type='model', local_dir='D:/models/faster-whisper-base')"
```

```python
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-medium', repo_type='model', local_dir='D:/models/faster-whisper-medium')"
```

Replace `D:/models/faster-whisper-base` with any directory of your choice.

### 3. Configure Environment Variables

Create a `.env` file in the project root (use `.env.example` as reference):

```
BASE=D:/models/faster-whisper-base
MEDIUM=D:/models/faster-whisper-medium
```

- `BASE` — path to your downloaded `faster-whisper-base` model directory
- `MEDIUM` — path to your downloaded `faster-whisper-medium` model directory

If you downloaded to the default cache directory, the path will be something like:

```
BASE=C:/Users/YourName/.cache/huggingface/hub/models--Systran--faster-whisper-base/snapshots/<hash>
```

To find the exact path, run:

```python
python -c "from huggingface_hub import snapshot_download; print(snapshot_download(repo_id='Systran/faster-whisper-base', repo_type='model'))"
```

### 4. Create Desktop Shortcut (Optional)

```
python create_shortcut.py
```

This places a **SpeechLab** shortcut on your Windows Desktop.

---

## Usage

**Option 1:** Double-click the SpeechLab desktop shortcut.

**Option 2:** Run from terminal:

```
python desktop.py
```

---

## Features

- **500+ speaking topics** across 5 categories (Technical, Abstract, Opinion, Storytelling, Interview)
- **Audio recording** with live waveform visualizer
- **Local transcription** via faster-whisper with word-level timestamps
- **Speech metrics**: WPM, articulation rate, filler density, repetition count, pause analysis, vocabulary diversity
- **Visual transcript** with highlighted fillers and repetitions
- **AI Coach panel** for pasting transcript into any external LLM
- **Session history** stored locally as JSON
- **Model selection** between base and medium whisper models
- **Parallel transcription** for recordings over 30 seconds

---

## Project Structure

```
speech-to-text/
├── backend/
│   ├── config.py            Centralized configuration
│   ├── topics.py            500+ speaking topics
│   ├── transcription.py     faster-whisper integration
│   ├── metrics.py           Speech metric computation
│   ├── audio_chunks.py      Audio splitting for parallel processing
│   └── main.py              FastAPI server
├── frontend/
│   ├── index.html           SPA dashboard
│   ├── css/styles.css        Dark theme design system
│   └── js/app.js            Frontend logic
├── .env.example             Environment variable template
├── desktop.py               Desktop launcher (PyWebView)
├── create_shortcut.py       Windows shortcut creator
└── requirements.txt         Python dependencies
```

---

## Tech Stack

- **Backend**: FastAPI, faster-whisper, pydub
- **Frontend**: Vanilla HTML/CSS/JS (SPA)
- **Desktop**: PyWebView
- **Models**: CTranslate2 (via faster-whisper)
