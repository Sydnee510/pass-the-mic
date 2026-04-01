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

st.set_page_config(page_title="Pass the Mic", page_icon="🎤", layout="wide")

# --- Custom Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #09090b;
        --bg-card: #18181b;
        --bg-card-hover: #1f1f23;
        --border: #27272a;
        --text-primary: #fafafa;
        --text-secondary: #a1a1aa;
        --text-muted: #71717a;
        --accent: #a855f7;
        --accent-light: #c084fc;
        --accent-glow: rgba(168, 85, 247, 0.15);
        --red: #ef4444;
        --cyan: #22d3ee;
    }

    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
    }

    /* Kill all Streamlit chrome */
    #MainMenu, footer, header,
    [data-testid="stSidebar"] { display: none !important; }
    .stDeployButton { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }

    /* ---- Hero ---- */
    .hero {
        text-align: center;
        padding: 3rem 1rem 1rem;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 4.5rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.05;
        margin: 0;
        letter-spacing: -0.03em;
    }
    .hero-title span {
        background: linear-gradient(135deg, var(--accent), var(--cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-sub {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-secondary);
        font-size: 1.15rem;
        margin-top: 0.75rem;
        line-height: 1.6;
    }

    /* ---- Mode Toggle ---- */
    .mode-toggle {
        display: flex;
        justify-content: center;
        gap: 0;
        margin: 2rem auto 0;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 4px;
        width: fit-content;
    }
    .mode-btn {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        color: var(--text-muted);
        background: transparent;
    }
    .mode-btn.active {
        background: var(--accent);
        color: white;
        box-shadow: 0 0 20px var(--accent-glow);
    }

    /* ---- Pill badges ---- */
    .pills {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 1.25rem;
        flex-wrap: wrap;
    }
    .pill {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--accent-light);
        background: var(--accent-glow);
        border: 1px solid rgba(168, 85, 247, 0.2);
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
    }

    /* ---- Section Headers ---- */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--accent-light);
        margin-bottom: 0.75rem;
    }

    /* ---- Cards ---- */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1rem;
    }
    .card:hover {
        border-color: rgba(168, 85, 247, 0.3);
    }

    /* ---- Mic recorder ---- */
    [data-testid="stAudioRecorder"] {
        display: flex;
        justify-content: center;
    }

    /* ---- File uploader ---- */
    [data-testid="stFileUploader"] {
        background: var(--bg-card);
        border: 2px dashed var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent);
    }

    /* ---- Transcript card ---- */
    .transcript-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 2rem;
        margin-top: 1.5rem;
    }
    .transcript-card h3 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--cyan);
        margin-bottom: 1rem;
    }
    .transcript-card p {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.05rem;
        line-height: 1.8;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
    }
    .speaker-label {
        color: var(--cyan);
        font-weight: 600;
        margin-right: 0.5rem;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* ---- Divider ---- */
    .divider {
        text-align: center;
        color: var(--text-muted);
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        margin: 2rem 0;
        position: relative;
    }
    .divider::before, .divider::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 40%;
        height: 1px;
        background: var(--border);
    }
    .divider::before { left: 0; }
    .divider::after { right: 0; }

    /* ---- Session cards ---- */
    .session-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s;
    }
    .session-card:hover {
        border-color: rgba(168, 85, 247, 0.3);
        background: var(--bg-card-hover);
    }
    .session-date {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .session-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0.3rem 0;
    }
    .session-preview {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }
    .session-tags {
        margin-top: 0.5rem;
        display: flex;
        gap: 0.25rem;
        flex-wrap: wrap;
    }
    .session-tag {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        font-weight: 500;
        color: var(--accent-light);
        background: var(--accent-glow);
        border: 1px solid rgba(168, 85, 247, 0.2);
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
    }

    /* ---- Streamlit overrides ---- */
    .stButton > button {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: var(--bg-card);
        color: var(--text-primary);
        padding: 0.5rem 1.25rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: var(--accent);
        background: var(--accent-glow);
    }
    .stDownloadButton > button {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        border-radius: 10px;
        background: var(--accent);
        color: white;
        border: none;
        padding: 0.5rem 1.25rem;
    }
    .stDownloadButton > button:hover {
        background: var(--accent-light);
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }
    .stCheckbox label {
        color: var(--text-secondary) !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stAlert {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
    }
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }
    .stCaption, [data-testid="stCaption"] {
        color: var(--text-muted) !important;
    }

    /* ---- Responsive ---- */
    @media (max-width: 768px) {
        .hero-title { font-size: 2.75rem; }
        .card { padding: 1.25rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- Mode toggle (stored in session state) ---
if "mode" not in st.session_state:
    st.session_state.mode = "Lyrics"

# --- Header ---
st.markdown("""
<div class="hero">
    <p class="hero-title">Pass the <span>Mic</span></p>
</div>
""", unsafe_allow_html=True)

# Mode toggle buttons
col_left, col_l, col_r, col_right = st.columns([2, 1, 1, 2])
with col_l:
    if st.button("Lyrics", key="mode_lyrics", use_container_width=True):
        st.session_state.mode = "Lyrics"
        st.rerun()
with col_r:
    if st.button("Podcast", key="mode_podcast", use_container_width=True):
        st.session_state.mode = "Podcast"
        st.rerun()

mode = st.session_state.mode

if mode == "Lyrics":
    hero_sub = "Record your bars, poems, and lyrics — get them transcribed instantly."
    pills = ["Nova-3", "Smart Format", "Diarization"]
else:
    hero_sub = "Record episodes and interviews — get speaker-labeled transcripts."
    pills = ["Nova-3", "Speaker Labels", "Show Notes"]

pills_html = "".join(f'<span class="pill">{p}</span>' for p in pills)
st.markdown(f"""
<div style="text-align:center;">
    <p class="hero-sub">{hero_sub}</p>
    <div class="pills">{pills_html}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- API Key ---
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

if not deepgram_api_key:
    st.warning("Set your `DEEPGRAM_API_KEY` in a `.env` file to get started.")
    st.code("echo 'DEEPGRAM_API_KEY=your_key_here' > .env", language="bash")
    st.stop()

deepgram = DeepgramClient(api_key=deepgram_api_key)


# --- Utility functions ---

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


def trim_audio(audio_bytes: bytes, start_sec: float, end_sec: float, ext: str = "wav") -> bytes:
    """Trim audio to a specific time range and return WAV bytes."""
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name
    tmp_out_path = tmp_in_path.rsplit(".", 1)[0] + "_trimmed.wav"
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(tmp_in_path)
        trimmed = clip.subclipped(start_sec, end_sec)
        trimmed.write_audiofile(tmp_out_path, logger=None)
        trimmed.close()
        clip.close()
        with open(tmp_out_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def get_audio_duration(audio_bytes: bytes, ext: str = "wav") -> float:
    """Get duration of audio in seconds."""
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(tmp_path)
        duration = clip.duration
        clip.close()
        return duration
    finally:
        os.unlink(tmp_path)


def transcribe(audio_data: bytes, mimetype: str) -> dict:
    """Send audio to Deepgram and return transcript with speaker data."""
    response = deepgram.listen.v1.media.transcribe_file(
        request=audio_data,
        model="nova-3",
        language="en",
        smart_format=True,
        paragraphs=True,
        diarize=True,
        utterances=True,
    )
    alt = response.results.channels[0].alternatives[0]
    plain_transcript = alt.transcript

    speakers = []
    paragraphs = alt.paragraphs
    if paragraphs and paragraphs.paragraphs:
        plain_transcript = "\n\n".join(
            " ".join(s.text for s in p.sentences)
            for p in paragraphs.paragraphs
        )
        for p in paragraphs.paragraphs:
            speakers.append({
                "speaker": p.speaker,
                "text": " ".join(s.text for s in p.sentences),
            })

    return {"transcript": plain_transcript, "speakers": speakers}


def get_speaker_name(speaker_num: int, guest_names: list) -> str:
    """Map a speaker number to a guest name or default label."""
    if speaker_num < len(guest_names) and guest_names[speaker_num].strip():
        return guest_names[speaker_num].strip()
    return f"Speaker {speaker_num + 1}"


def format_speaker_transcript(speakers: list, guest_names: list) -> str:
    """Build plain-text speaker-labeled transcript for export."""
    lines = []
    for seg in speakers:
        name = get_speaker_name(seg["speaker"], guest_names)
        lines.append(f"{name}: {seg['text']}")
    return "\n\n".join(lines)


def save_session(title: str, audio_data: bytes, result: dict, source: str,
                 meta_extra: dict = None):
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
        "transcript": result["transcript"],
        "speakers": result["speakers"],
        "audio_file": f"{filename}.wav",
    }
    if meta_extra:
        meta.update(meta_extra)

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


def show_transcript(result: dict, guest_names: list = None):
    """Display transcript in a styled card, with speaker labels in Podcast mode."""
    if mode == "Podcast" and result["speakers"]:
        paras = []
        for seg in result["speakers"]:
            name = get_speaker_name(seg["speaker"], guest_names or [])
            paras.append(f'<p><span class="speaker-label">{name}:</span>{seg["text"]}</p>')
        body = "".join(paras)
    else:
        body = "".join(f"<p>{p}</p>" for p in result["transcript"].split("\n\n"))

    st.markdown(f"""
    <div class="transcript-card">
        <h3>Transcript</h3>
        {body}
    </div>
    """, unsafe_allow_html=True)


def handle_result(audio_data: bytes, mimetype: str, source: str):
    """Transcribe audio, display result, and offer save/download."""
    st.audio(audio_data, format=mimetype)

    with st.spinner("Transcribing..."):
        result = transcribe(audio_data, mimetype)

    if not result["transcript"].strip():
        st.info("No speech detected. Try speaking louder or closer to your mic.")
        return

    # --- Podcast: guest names ---
    guest_names = []
    if mode == "Podcast" and result["speakers"]:
        unique_speakers = sorted(set(s["speaker"] for s in result["speakers"]))
        guest_input = st.text_input(
            f"Name the speakers ({len(unique_speakers)} detected, comma-separated)",
            placeholder="e.g. Host, Jane, Mike",
            key=f"guests_{source}",
        )
        if guest_input:
            guest_names = [n.strip() for n in guest_input.split(",")]

    show_transcript(result, guest_names)

    # --- Session title ---
    if mode == "Lyrics":
        title_placeholder = "e.g. Freestyle #3, Spoken Word Draft, Verse 1..."
    else:
        title_placeholder = "e.g. Episode 12, Interview with Jane, Pilot Episode..."

    title = st.text_input(
        "Name this session",
        placeholder=title_placeholder,
        key=f"title_{source}",
    )

    # --- Podcast: episode metadata ---
    ep_number = None
    ep_description = ""
    ep_tags = ""
    if mode == "Podcast":
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            ep_number = st.number_input(
                "Episode number",
                min_value=1,
                step=1,
                value=None,
                key=f"ep_{source}",
            )
        with col_meta2:
            ep_tags = st.text_input(
                "Tags (comma-separated)",
                placeholder="e.g. AI, interview, tech",
                key=f"tags_{source}",
            )
        ep_description = st.text_area(
            "Episode description",
            placeholder="A short summary of this episode...",
            max_chars=500,
            height=80,
            key=f"desc_{source}",
        )

    # --- Action buttons ---
    if mode == "Podcast" and result["speakers"]:
        col1, col2, col3 = st.columns(3)
    else:
        col1, col2 = st.columns(2)
        col3 = None

    with col1:
        st.download_button(
            label="Download Audio",
            data=audio_data,
            file_name=f"{title or 'recording'}.wav",
            mime="audio/wav",
            key=f"dl_audio_{source}",
        )

    if col3:
        with col2:
            export_text = format_speaker_transcript(result["speakers"], guest_names)
            st.download_button(
                label="Download Transcript",
                data=export_text,
                file_name=f"{title or 'transcript'}.txt",
                mime="text/plain",
                key=f"dl_transcript_{source}",
            )
        save_col = col3
    else:
        save_col = col2

    with save_col:
        if st.button("Save Session", key=f"save_{source}"):
            meta_extra = {"mode": mode}
            if mode == "Podcast":
                meta_extra["guest_names"] = guest_names
                if ep_number:
                    meta_extra["episode_number"] = ep_number
                if ep_description:
                    meta_extra["description"] = ep_description
                if ep_tags:
                    meta_extra["tags"] = [t.strip() for t in ep_tags.split(",") if t.strip()]
            save_session(title or "Untitled", audio_data, result, source, meta_extra)
            st.success("Saved!")
            st.rerun()


# --- Main Content ---
col_main_l, col_main, col_main_r = st.columns([1, 3, 1])

with col_main:
    # --- Record ---
    st.markdown('<p class="section-header">Record</p>', unsafe_allow_html=True)
    if mode == "Podcast":
        st.caption("For full episodes, upload your audio file below.")

    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#a855f7",
        pause_threshold=300,
    )

    st.markdown('<div class="divider">or</div>', unsafe_allow_html=True)

    # --- Upload ---
    upload_label = "Upload a Track" if mode == "Lyrics" else "Upload an Episode"
    st.markdown(f'<p class="section-header">{upload_label}</p>', unsafe_allow_html=True)
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
            ext = "wav"
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

        # --- Trim option for long files ---
        with st.spinner("Reading audio duration..."):
            duration = get_audio_duration(file_bytes, ext)
        duration_min = duration / 60

        if duration_min > 5:
            st.caption(f"File duration: **{int(duration_min)}m {int(duration % 60)}s**")
            trim_enabled = st.checkbox("Trim audio before transcribing", value=False, key="trim_toggle")
            if trim_enabled:
                col_start, col_end = st.columns(2)
                with col_start:
                    start_min = st.number_input("Start (minutes)", min_value=0.0, max_value=duration_min, value=0.0, step=1.0, key="trim_start")
                with col_end:
                    end_min = st.number_input("End (minutes)", min_value=0.0, max_value=duration_min, value=min(5.0, duration_min), step=1.0, key="trim_end")
                if st.button("Trim & Transcribe", key="trim_btn"):
                    with st.spinner("Trimming audio..."):
                        file_bytes = trim_audio(file_bytes, start_min * 60, end_min * 60, ext)
                    mimetype = "audio/wav"
                    handle_result(file_bytes, mimetype, "upload")
            else:
                handle_result(file_bytes, mimetype, "upload")
        else:
            handle_result(file_bytes, mimetype, "upload")

    # --- Past Sessions ---
    sessions = load_sessions()
    if sessions:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-header">Your Sessions</p>', unsafe_allow_html=True)

        for session in sessions:
            dt = datetime.fromisoformat(session["timestamp"])
            date_str = dt.strftime("%b %d, %Y &bull; %I:%M %p")

            title_display = session["title"]
            session_mode = session.get("mode", "Lyrics")
            ep_num = session.get("episode_number")
            if ep_num:
                title_display = f"Ep. {ep_num} — {title_display}"

            preview = session["transcript"][:150]
            if len(session["transcript"]) > 150:
                preview += "..."

            tags_html = ""
            session_tags = session.get("tags", [])
            if session_tags:
                tag_spans = "".join(f'<span class="session-tag">{t}</span>' for t in session_tags)
                tags_html = f'<div class="session-tags">{tag_spans}</div>'

            mode_badge = f'<span class="session-tag">{session_mode}</span>'

            st.markdown(f"""
            <div class="session-card">
                <div class="session-date">{date_str} {mode_badge}</div>
                <div class="session-title">{title_display}</div>
                <div class="session-preview">{preview}</div>
                {tags_html}
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
