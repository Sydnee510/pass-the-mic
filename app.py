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

# --- Load external stylesheet ---
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Hero ---
st.markdown("""
<div class="hero">
    <svg class="hero-logo" width="28" height="28" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <rect x="52" y="18" width="16" height="36" rx="8" fill="#3c3c42"/>
        <path d="M36 48 Q36 72 60 72 Q84 72 84 48" fill="none" stroke="#3c3c42" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="60" y1="72" x2="60" y2="85" stroke="#3c3c42" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="46" y1="85" x2="74" y2="85" stroke="#3c3c42" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="16" y1="54" x2="16" y2="64" stroke="#3c3c42" stroke-width="3" stroke-linecap="round" opacity="0.45"/>
        <line x1="25" y1="46" x2="25" y2="72" stroke="#3c3c42" stroke-width="3" stroke-linecap="round" opacity="0.38"/>
        <line x1="95" y1="46" x2="95" y2="72" stroke="#3c3c42" stroke-width="3" stroke-linecap="round" opacity="0.38"/>
        <line x1="104" y1="54" x2="104" y2="64" stroke="#3c3c42" stroke-width="3" stroke-linecap="round" opacity="0.45"/>
    </svg>
    <p class="hero-title">Pass the Mic</p>
    <p class="hero-sub">Record. Transcribe. Create.</p>
</div>
""", unsafe_allow_html=True)

# --- Mode Toggle ---
mode = st.radio("Mode", ["Lyrics", "Podcast", "Book"], horizontal=True, label_visibility="collapsed")

if mode == "Lyrics":
    sub = "Spit your bars, read your poems, or freestyle — we'll catch every word."
    pills = ["Nova-3", "Smart Format", "Diarization"]
elif mode == "Podcast":
    sub = "Upload episodes and interviews. Get speaker-labeled transcripts instantly."
    pills = ["Nova-3", "Speaker Labels", "Show Notes"]
else:
    sub = "Read aloud your chapters and manuscripts. Get narrator-ready transcripts."
    pills = ["Nova-3", "Chapters", "Narrator Mode"]

pills_html = "".join(f'<span class="pill">{p}</span>' for p in pills)
st.markdown(f"""
<div style="text-align:center; max-width:560px; margin:0 auto; position:relative; z-index:1;">
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


# --- Utility Functions ---

def extract_audio_from_video(video_bytes, ext):
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


def trim_audio(audio_bytes, start_sec, end_sec, ext="wav"):
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


def get_audio_duration(audio_bytes, ext="wav"):
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


def transcribe(audio_data, mimetype):
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
            " ".join(s.text for s in p.sentences) for p in paragraphs.paragraphs
        )
        for p in paragraphs.paragraphs:
            speakers.append({
                "speaker": p.speaker,
                "text": " ".join(s.text for s in p.sentences),
            })
    return {"transcript": plain_transcript, "speakers": speakers}


def get_speaker_name(speaker_num, guest_names):
    if speaker_num < len(guest_names) and guest_names[speaker_num].strip():
        return guest_names[speaker_num].strip()
    return f"Speaker {speaker_num + 1}"


def format_speaker_transcript(speakers, guest_names):
    lines = []
    for seg in speakers:
        name = get_speaker_name(seg["speaker"], guest_names)
        lines.append(f"{name}: {seg['text']}")
    return "\n\n".join(lines)


def save_session(title, audio_data, result, source, meta_extra=None):
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
    sessions = []
    for fname in os.listdir(RECORDINGS_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(RECORDINGS_DIR, fname)) as f:
                sessions.append(json.load(f))
    sessions.sort(key=lambda s: s["timestamp"], reverse=True)
    return sessions


def show_transcript(result, guest_names=None):
    if mode == "Book":
        body = "".join(f'<p class="book-para">{p}</p>' for p in result["transcript"].split("\n\n"))
    elif mode == "Podcast" and result["speakers"]:
        paras = []
        for seg in result["speakers"]:
            name = get_speaker_name(seg["speaker"], guest_names or [])
            paras.append(f'<p><span class="speaker-label">{name}:</span> {seg["text"]}</p>')
        body = "".join(paras)
    else:
        body = "".join(f"<p>{p}</p>" for p in result["transcript"].split("\n\n"))

    st.markdown(f"""
    <div class="transcript-card">
        <h3>Transcript</h3>
        {body}
    </div>
    """, unsafe_allow_html=True)


def show_ai_bar():
    st.markdown("""
    <div class="ai-bar">
        <div class="ai-dots">
            <div class="ai-dot"></div>
            <div class="ai-dot"></div>
            <div class="ai-dot"></div>
        </div>
        AI is transcribing your audio with Nova-3...
    </div>
    """, unsafe_allow_html=True)


def handle_result(audio_data, mimetype, source):
    st.audio(audio_data, format=mimetype)

    ai_placeholder = st.empty()
    with ai_placeholder.container():
        show_ai_bar()
    result = transcribe(audio_data, mimetype)
    ai_placeholder.empty()

    if not result["transcript"].strip():
        st.info("No speech detected. Try speaking louder or closer to your mic.")
        return

    # Podcast: guest names
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

    # Session title
    if mode == "Lyrics":
        placeholder = "e.g. Freestyle #3, Spoken Word Draft, Verse 1..."
    elif mode == "Podcast":
        placeholder = "e.g. Episode 12, Interview with Jane, Pilot Episode..."
    else:
        placeholder = "e.g. Chapter 1: The Beginning, Opening Monologue..."

    title = st.text_input("Name this session", placeholder=placeholder, key=f"title_{source}")

    # Mode-specific metadata
    ep_number = None
    ep_description = ""
    ep_tags = ""
    chapter_number = None
    chapter_title = ""

    if mode == "Podcast":
        c1, c2 = st.columns(2)
        with c1:
            ep_number = st.number_input("Episode number", min_value=1, step=1, value=None, key=f"ep_{source}")
        with c2:
            ep_tags = st.text_input("Tags (comma-separated)", placeholder="e.g. AI, interview, tech", key=f"tags_{source}")
        ep_description = st.text_area("Episode description", placeholder="A short summary...", max_chars=500, height=80, key=f"desc_{source}")
    elif mode == "Book":
        c1, c2 = st.columns(2)
        with c1:
            chapter_number = st.number_input("Chapter number", min_value=1, step=1, value=None, key=f"ch_{source}")
        with c2:
            chapter_title = st.text_input("Chapter title", placeholder="e.g. The Beginning", key=f"chtitle_{source}")

    # Action buttons
    if mode == "Podcast" and result["speakers"]:
        col1, col2, col3 = st.columns(3)
    else:
        col1, col2 = st.columns(2)
        col3 = None

    with col1:
        st.download_button("Download Audio", data=audio_data, file_name=f"{title or 'recording'}.wav", mime="audio/wav", key=f"dl_audio_{source}")

    if col3:
        with col2:
            export_text = format_speaker_transcript(result["speakers"], guest_names)
            st.download_button("Download Transcript", data=export_text, file_name=f"{title or 'transcript'}.txt", mime="text/plain", key=f"dl_transcript_{source}")
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
            elif mode == "Book":
                if chapter_number:
                    meta_extra["chapter_number"] = chapter_number
                if chapter_title:
                    meta_extra["chapter_title"] = chapter_title
            save_session(title or "Untitled", audio_data, result, source, meta_extra)
            st.success("Saved!")
            st.rerun()


# ============================================
# Main Layout
# ============================================
_, col_main, _ = st.columns([1, 3, 1])

with col_main:
    upload_label = "Upload a Track" if mode == "Lyrics" else ("Upload an Episode" if mode == "Podcast" else "Upload a Chapter")

    # --- Glass Record Panel (open) ---
    st.markdown("""
    <div class="record-panel">
        <div class="panel-label">
            <span class="status-dot"></span> Record a session
        </div>
        <div class="waveform-area">
            <div class="waveform-placeholder">
                <div style="font-size:1.8rem;margin-bottom:0.4rem;opacity:0.25;">🎙</div>
                <div>Tap the mic to begin recording</div>
            </div>
            <div class="timer">0:00</div>
        </div>
    """, unsafe_allow_html=True)

    # The Streamlit recorder sits inside the controls row
    st.markdown('<div class="controls-row">', unsafe_allow_html=True)
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ff3b30",
        neutral_color="#888890",
        pause_threshold=300,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider">or</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="upload-zone-label">
            <div class="upload-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12 16V4M12 4L8 8M12 4L16 8" stroke="#888890" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M4 14V18C4 19.1 4.9 20 6 20H18C19.1 20 20 19.1 20 18V14" stroke="#888890" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <p class="upload-title">{upload_label}</p>
            <p class="upload-formats">WAV · MP3 · MP4 · M4A · FLAC · OGG · WEBM · MOV</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Audio or video files",
        type=["wav", "mp3", "mp4", "m4a", "flac", "ogg", "webm", "mov", "avi", "mkv"],
        label_visibility="collapsed",
    )

    # Close record panel
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Results ---
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
            mime_map = {"wav": "audio/wav", "mp3": "audio/mpeg", "m4a": "audio/mp4", "flac": "audio/flac", "ogg": "audio/ogg"}
            mimetype = mime_map.get(ext, "audio/wav")

        with st.spinner("Reading audio duration..."):
            duration = get_audio_duration(file_bytes, ext)
        duration_min = duration / 60

        if duration_min > 5:
            st.caption(f"File duration: **{int(duration_min)}m {int(duration % 60)}s**")
            trim_enabled = st.checkbox("Trim audio before transcribing", value=False, key="trim_toggle")
            if trim_enabled:
                c1, c2 = st.columns(2)
                with c1:
                    start_min = st.number_input("Start (min)", min_value=0.0, max_value=duration_min, value=0.0, step=1.0, key="trim_start")
                with c2:
                    end_min = st.number_input("End (min)", min_value=0.0, max_value=duration_min, value=min(5.0, duration_min), step=1.0, key="trim_end")
                if st.button("Trim & Transcribe", key="trim_btn"):
                    with st.spinner("Trimming audio..."):
                        file_bytes = trim_audio(file_bytes, start_min * 60, end_min * 60, ext)
                    handle_result(file_bytes, "audio/wav", "upload")
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

            # Episode number for podcasts
            ep_num = session.get("episode_number")
            if ep_num:
                title_display = f"Ep. {ep_num} — {title_display}"

            # Chapter number and title for books
            chapter_num = session.get("chapter_number")
            chapter_title_val = session.get("chapter_title", "")
            if chapter_num:
                title_display = f"Ch. {chapter_num} — {title_display}"
                if chapter_title_val:
                    title_display += f": {chapter_title_val}"

            preview = session["transcript"][:150]
            if len(session["transcript"]) > 150:
                preview += "..."

            tags_html = ""
            session_tags = session.get("tags", [])
            if session_tags:
                tag_spans = "".join(f'<span class="session-tag">{t}</span>' for t in session_tags)
                tags_html = f'<div class="session-tags">{tag_spans}</div>'

            badge_class = session_mode.lower()
            mode_badge = f'<span class="badge {badge_class}">{session_mode}</span>'

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
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.audio(audio_data, format="audio/wav")
                with c2:
                    st.download_button(
                        "Download", data=audio_data,
                        file_name=f"{session['title']}.wav",
                        mime="audio/wav",
                        key=f"dl_{session['timestamp']}",
                    )

    # Bottom notch
    st.markdown("""
    <div class="bottom-notch">
        <div class="bottom-notch-bar"></div>
    </div>
    """, unsafe_allow_html=True)
