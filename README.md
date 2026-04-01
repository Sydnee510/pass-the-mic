# Pass the Mic

A voice-to-text app for creators — poets, rappers, lyricists, and podcasters. Record or upload audio, get instant transcripts powered by Deepgram's Nova-3 speech-to-text model. Switch between **Lyrics** and **Podcast** modes for a tailored experience.

## Use Cases

### Lyrics Mode
Writers and performers often freestyle or workshop lyrics out loud but lose their best lines because they weren't written down. Hit record, spit your bars, and get a clean transcript instantly.

### Podcast Mode
Podcasters and interviewers can upload episodes and get speaker-labeled transcripts — perfect for show notes, accessibility, clip discovery, and SEO. Name your speakers, tag episodes, and export transcripts as text files.

## Features

- **Deepgram Nova-3** — latest and most accurate speech-to-text model
- **Smart formatting** — automatic punctuation, casing, and number formatting
- **Speaker diarization** — identifies and labels different speakers
- **Guest name mapping** — replace "Speaker 1" with actual names (Podcast mode)
- **Episode metadata** — episode number, description, and tags (Podcast mode)
- **Transcript export** — download speaker-labeled transcripts as TXT (Podcast mode)
- **Session library** — saved recordings with audio playback and transcript preview
- **Video support** — upload MP4, MOV, AVI, MKV and audio is extracted automatically
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

### 4. Add your Deepgram API key

Sign up at [console.deepgram.com](https://console.deepgram.com) and grab an API key, then:

```bash
cp .env.example .env
```

Open `.env` and replace `your_api_key_here` with your actual key.

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**. Use the sidebar to switch between Lyrics and Podcast modes.

## Tech Stack

- **Python** + **Streamlit** — frontend and app framework
- **Deepgram SDK** — speech-to-text via the pre-recorded REST API (Nova-3)
- **audio-recorder-streamlit** — in-browser mic recording
- **moviepy** — audio extraction from video files

## Project Structure

```
pass-the-mic/
├── app.py              # Main Streamlit application
├── recordings/         # Saved audio files and session metadata (JSON)
├── requirements.txt    # Python dependencies
├── .env.example        # API key template
└── .gitignore          # Ignores .env, venv, pycache, recordings
```
