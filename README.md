# Pass the Mic

A voice-to-text app for poets, rappers, and lyricists to record their bars, poems, and spoken word — and get them transcribed instantly. Built with Streamlit and powered by Deepgram's Nova-3 speech-to-text model.

## Use Case

Writers and performers often freestyle or workshop lyrics out loud but lose their best lines because they weren't written down. **Pass the Mic** lets you:

- Hit record, spit your bars, and get a clean transcript with punctuation and casing
- Upload existing audio recordings to transcribe
- Save sessions with titles so you can build a library of your work
- Download audio files to share or archive
- Review past sessions with transcripts and playback

## Features

- **Deepgram Nova-3** — latest and most accurate speech-to-text model
- **Smart formatting** — automatic punctuation, casing, and number formatting
- **Speaker diarization** — identifies different speakers in a session
- **Session library** — saved recordings with audio playback and transcript preview
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

The app will open at **http://localhost:8501**.

## Tech Stack

- **Python** + **Streamlit** — frontend and app framework
- **Deepgram SDK** — speech-to-text via the pre-recorded REST API
- **audio-recorder-streamlit** — in-browser mic recording

## Project Structure

```
pass-the-mic/
├── app.py              # Main Streamlit application
├── recordings/         # Saved audio files and session metadata
├── requirements.txt    # Python dependencies
├── .env.example        # API key template
└── .gitignore          # Ignores .env, venv, pycache
```
