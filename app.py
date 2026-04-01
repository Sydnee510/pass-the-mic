import streamlit as st
from audio_recorder_streamlit import audio_recorder
from deepgram import DeepgramClient
from dotenv import load_dotenv
from datetime import datetime
import json
import os
import tempfile

load_dotenv()

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

st.set_page_config(page_title="Pass the Mic", page_icon="🎤", layout="centered")

# --- Custom Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e);
        color: #e0e0e0;
    }

    /* Header */
    .hero {
        text-align: center;
        padding: 2rem 0 0.5rem;
    }
    .hero h1 {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d2ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .hero p {
        font-family: 'Inter', sans-serif;
        color: #8892b0;
        font-size: 1.05rem;
    }
    .badge {
        display: inline-block;
        background: rgba(123, 47, 247, 0.15);
        border: 1px solid rgba(123, 47, 247, 0.3);
        color: #b794f6;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-family: 'Inter', sans-serif;
        margin-top: 0.5rem;
    }

    /* Section labels */
    .section-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #7b2ff7;
        margin-bottom: 0.5rem;
    }

    /* Transcript card */
    .transcript-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }
    .transcript-card h3 {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #00d2ff;
        margin-bottom: 0.75rem;
    }
    .transcript-card p {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #e0e0e0;
    }

    /* Mic recorder centering */
    [data-testid="stAudioRecorder"] {
        display: flex;
        justify-content: center;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px dashed rgba(123, 47, 247, 0.3);
        border-radius: 12px;
        padding: 1rem;
    }

    /* Divider */
    .divider {
        text-align: center;
        color: #4a4a6a;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        margin: 1.5rem 0;
    }

    /* Past session card */
    .session-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .session-card .session-date {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #7b2ff7;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .session-card .session-title {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: #e0e0e0;
        margin: 0.25rem 0;
    }
    .session-card .session-preview {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #8892b0;
        line-height: 1.5;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Info/warning boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="hero">
    <h1>Pass the Mic</h1>
    <p>Record your bars, poems, and lyrics — get them transcribed instantly.</p>
    <span class="badge">Deepgram Nova-3 &bull; Smart Format &bull; Diarization</span>
</div>
""", unsafe_allow_html=True)

deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

if not deepgram_api_key:
    st.warning("Set your `DEEPGRAM_API_KEY` in a `.env` file to get started.")
    st.code("echo 'DEEPGRAM_API_KEY=your_key_here' > .env", language="bash")
    st.stop()

deepgram = DeepgramClient(api_key=deepgram_api_key)


def extract_audio_from_video(video_bytes: bytes, ext: str) -> bytes:
    """Extract audio from a video file and return WAV bytes."""
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp_in:
        tmp_in.write(video_bytes)
        tmp_in_path = tmp_in.name
    tmp_out_path = tmp_in_path.rsplit(".", 1)[0] + ".wav"
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(tmp_in_path)
        clip.write_audiofile(tmp_out_path, logger=None)
        clip.close()
        with open(tmp_out_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def transcribe(audio_data: bytes, mimetype: str) -> str:
    """Send audio to Deepgram's pre-recorded API and return the transcript."""
    response = deepgram.listen.v1.media.transcribe_file(
        request=audio_data,
        model="nova-3",
        language="en",
        smart_format=True,
        paragraphs=True,
        diarize=True,
    )
    paragraphs = response.results.channels[0].alternatives[0].paragraphs
    if paragraphs and paragraphs.paragraphs:
        return "\n\n".join(
            " ".join(s.text for s in p.sentences)
            for p in paragraphs.paragraphs
        )
    return response.results.channels[0].alternatives[0].transcript


def save_session(title: str, audio_data: bytes, transcript: str, source: str):
    """Save audio and transcript to the recordings directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = title.strip().lower().replace(" ", "_")[:40] if title.strip() else timestamp
    filename = f"{timestamp}_{slug}"

    audio_path = os.path.join(RECORDINGS_DIR, f"{filename}.wav")
    meta_path = os.path.join(RECORDINGS_DIR, f"{filename}.json")

    with open(audio_path, "wb") as f:
        f.write(audio_data)

    meta = {
        "title": title.strip() or "Untitled",
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "transcript": transcript,
        "audio_file": f"{filename}.wav",
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return audio_path


def load_sessions():
    """Load all saved sessions, sorted newest first."""
    sessions = []
    for fname in os.listdir(RECORDINGS_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(RECORDINGS_DIR, fname)) as f:
                sessions.append(json.load(f))
    sessions.sort(key=lambda s: s["timestamp"], reverse=True)
    return sessions


def show_transcript(transcript: str):
    """Display transcript in a styled card."""
    paragraphs_html = "".join(f"<p>{p}</p>" for p in transcript.split("\n\n"))
    st.markdown(f"""
    <div class="transcript-card">
        <h3>Transcript</h3>
        {paragraphs_html}
    </div>
    """, unsafe_allow_html=True)


def handle_result(audio_data: bytes, mimetype: str, source: str):
    """Transcribe audio, display result, and offer save/download."""
    st.audio(audio_data, format=mimetype)

    with st.spinner("Transcribing..."):
        transcript = transcribe(audio_data, mimetype)

    if not transcript.strip():
        st.info("No speech detected. Try speaking louder or closer to your mic.")
        return

    show_transcript(transcript)

    # Title input and actions
    title = st.text_input(
        "Name this session",
        placeholder="e.g. Freestyle #3, Spoken Word Draft, Verse 1...",
        key=f"title_{source}",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download Audio",
            data=audio_data,
            file_name=f"{title or 'recording'}.wav",
            mime="audio/wav",
        )
    with col2:
        if st.button("Save Session", key=f"save_{source}"):
            save_session(title or "Untitled", audio_data, transcript, source)
            st.success("Saved!")
            st.rerun()


# --- Mic Recording ---
st.markdown('<p class="section-label">Record</p>', unsafe_allow_html=True)

audio_bytes = audio_recorder(
    text="",
    recording_color="#e74c3c",
    neutral_color="#7b2ff7",
    pause_threshold=300,
)

st.markdown('<div class="divider">&#8212; or &#8212;</div>', unsafe_allow_html=True)

# --- File Upload ---
st.markdown('<p class="section-label">Upload a Track</p>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Audio or video files",
    type=["wav", "mp3", "mp4", "m4a", "flac", "ogg", "webm", "mov", "avi", "mkv"],
    label_visibility="collapsed",
)

# --- Handle results ---
if audio_bytes:
    handle_result(audio_bytes, "audio/wav", "mic")

if uploaded_file:
    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    video_exts = {"mp4", "webm", "mov", "avi", "mkv"}
    if ext in video_exts:
        with st.spinner("Extracting audio from video..."):
            file_bytes = extract_audio_from_video(file_bytes, ext)
        mimetype = "audio/wav"
    else:
        mime_map = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "m4a": "audio/mp4",
            "flac": "audio/flac",
            "ogg": "audio/ogg",
        }
        mimetype = mime_map.get(ext, "audio/wav")
    handle_result(file_bytes, mimetype, "upload")

# --- Past Sessions ---
sessions = load_sessions()
if sessions:
    st.markdown("---")
    st.markdown('<p class="section-label">Your Sessions</p>', unsafe_allow_html=True)

    for session in sessions:
        dt = datetime.fromisoformat(session["timestamp"])
        date_str = dt.strftime("%b %d, %Y &bull; %I:%M %p")
        preview = session["transcript"][:150]
        if len(session["transcript"]) > 150:
            preview += "..."

        st.markdown(f"""
        <div class="session-card">
            <div class="session-date">{date_str}</div>
            <div class="session-title">{session["title"]}</div>
            <div class="session-preview">{preview}</div>
        </div>
        """, unsafe_allow_html=True)

        audio_path = os.path.join(RECORDINGS_DIR, session["audio_file"])
        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.audio(audio_data, format="audio/wav")
            with col2:
                st.download_button(
                    label="Download",
                    data=audio_data,
                    file_name=f"{session['title']}.wav",
                    mime="audio/wav",
                    key=f"dl_{session['timestamp']}",
                )
