# Pass the Mic

A voice-to-text app for creators — poets, rappers, lyricists, podcasters, and writers. Record or upload audio, get instant transcripts powered by Deepgram's Nova-3 speech-to-text model. Switch between **Lyrics**, **Podcast**, and **Book** modes for a tailored experience.

## Use Cases

### Lyrics Mode
Writers and performers often freestyle or workshop lyrics out loud but lose their best lines because they weren't written down. Hit record, spit your bars, and get a clean transcript instantly.

### Podcast Mode
Podcasters and interviewers can upload episodes and get speaker-labeled transcripts — perfect for show notes, accessibility, clip discovery, and SEO. Name your speakers, tag episodes, and export transcripts as text files.

### Book Mode
Authors and writers can read their chapters and manuscripts aloud to get clean, publish-ready transcripts. Whether you're drafting a novel, dictating a memoir, or converting handwritten work into digital text — speak it and get a formatted transcript ready for editing and publishing.

## Features

- **Deepgram Nova-3** — latest and most accurate speech-to-text model
- **Smart formatting** — automatic punctuation, casing, and number formatting
- **Speaker diarization** — identifies and labels different speakers
- **Guest name mapping** — replace "Speaker 1" with actual names (Podcast mode)
- **Episode metadata** — episode number, description, and tags (Podcast mode)
- **Chapter metadata** — chapter number and title (Book mode)
- **Transcript export** — download speaker-labeled transcripts as TXT (Podcast mode)
- **Google Drive storage** — sessions saved to your personal Drive (no database needed)
- **Google OAuth** — sign in with Google, each user's files stay private
- **Session library** — saved recordings with transcript preview
- **Video support** — upload MP4, MOV, AVI, MKV and audio is extracted automatically
- **Audio trimming** — trim long files before transcribing
- **Download** — export your audio files anytime

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/sydnee510/pass-the-mic.git
cd pass-the-mic
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

- **`DEEPGRAM_API_KEY`** — Sign up at [console.deepgram.com](https://console.deepgram.com) and grab an API key
- **`GOOGLE_CLIENT_ID`** and **`GOOGLE_CLIENT_SECRET`** — For Google Drive session storage (see below)
- **`SECRET_KEY`** — Any random string for session encryption

#### Google Drive Setup (for saving sessions)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project (or select an existing one)
3. Enable the **Google Drive API**
4. Go to **Credentials** > **Create Credentials** > **OAuth 2.0 Client ID**
5. Set application type to **Web application**
6. Add `http://localhost:8000/auth/callback` to **Authorized redirect URIs**
7. Copy your Client ID and Client Secret into `.env`

### 5. Run the app

There are two ways to run Pass the Mic:

**FastAPI (recommended)** — custom HTML frontend with glass UI, real browser mic recording, and full API:

```bash
python3 -m uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000**

**Streamlit (legacy)** — the original Streamlit-based UI:

```bash
streamlit run app.py
```

Open **http://localhost:8501**

Both versions share the same backend logic via `core.py` and the same `recordings/` directory.

## Tech Stack

- **FastAPI** + **Uvicorn** — API server (primary frontend)
- **Streamlit** — legacy frontend
- **Deepgram SDK** — speech-to-text via the pre-recorded REST API (Nova-3)
- **Google OAuth 2.0** + **Google Drive API** — user authentication and session storage
- **Authlib** — OAuth client for Starlette/FastAPI
- **MediaRecorder API** — in-browser mic recording (FastAPI version)
- **audio-recorder-streamlit** — in-browser mic recording (Streamlit version)
- **moviepy** — audio extraction from video files

## Project Structure

```
pass-the-mic/
├── core.py             # Shared backend logic (transcription, sessions, audio utils)
├── main.py             # FastAPI entry point (serves index.html + API endpoints)
├── index.html          # Standalone HTML/CSS/JS frontend (glass UI)
├── app.py              # Streamlit frontend (legacy)
├── styles.css          # Streamlit custom styles (legacy)
├── recordings/         # Saved audio files and session metadata (JSON)
├── images/             # Design assets and prototypes
├── requirements.txt    # Python dependencies
├── .env.example        # API key template
└── .gitignore          # Ignores .env, venv, pycache, recordings
```
