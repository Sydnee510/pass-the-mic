from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os

from core import (
    transcribe, save_session, load_sessions,
    extract_audio_from_video, trim_audio,
    RECORDINGS_DIR,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/recordings", StaticFiles(directory=RECORDINGS_DIR), name="recordings")


@app.get("/")
def root():
    return FileResponse("index.html")


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    mode: str = Form(default="Lyrics"),
):
    audio_bytes = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "wav"
    video_exts = {"mp4", "webm", "mov", "avi", "mkv"}

    if ext in video_exts:
        audio_bytes = extract_audio_from_video(audio_bytes, ext)
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

    result = transcribe(audio_bytes, mimetype)
    return JSONResponse(result)


@app.post("/trim")
async def trim_audio_endpoint(
    file: UploadFile = File(...),
    start_sec: float = Form(...),
    end_sec: float = Form(...),
):
    audio_bytes = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "wav"
    trimmed = trim_audio(audio_bytes, start_sec, end_sec, ext)
    result = transcribe(trimmed, "audio/wav")
    return JSONResponse(result)


@app.post("/save")
async def save_session_endpoint(
    file: UploadFile = File(...),
    title: str = Form(default="Untitled"),
    mode: str = Form(default="Lyrics"),
    transcript: str = Form(...),
    speakers: str = Form(default="[]"),
    guest_names: str = Form(default="[]"),
    episode_number: str = Form(default=""),
    episode_description: str = Form(default=""),
    episode_tags: str = Form(default=""),
    chapter_number: str = Form(default=""),
    chapter_title: str = Form(default=""),
):
    audio_bytes = await file.read()
    result = {
        "transcript": transcript,
        "speakers": json.loads(speakers),
    }
    meta_extra = {"mode": mode}

    if mode == "Podcast":
        meta_extra["guest_names"] = json.loads(guest_names)
        if episode_number:
            try:
                meta_extra["episode_number"] = int(episode_number)
            except ValueError:
                pass
        if episode_description:
            meta_extra["description"] = episode_description
        if episode_tags:
            meta_extra["tags"] = [
                t.strip() for t in episode_tags.split(",") if t.strip()
            ]

    if mode == "Book":
        if chapter_number:
            try:
                meta_extra["chapter_number"] = int(chapter_number)
            except ValueError:
                pass
        if chapter_title:
            meta_extra["chapter_title"] = chapter_title

    audio_path = save_session(title, audio_bytes, result, "upload", meta_extra)
    return JSONResponse({"status": "saved", "audio_path": audio_path})


@app.get("/sessions")
def get_sessions():
    return JSONResponse(load_sessions())
