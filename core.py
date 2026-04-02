from deepgram import DeepgramClient
from dotenv import load_dotenv
from datetime import datetime
import json
import os
import tempfile

load_dotenv()

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))


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
