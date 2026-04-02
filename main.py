from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from google.oauth2.credentials import Credentials
from datetime import datetime
import json
import os

from core import (
    transcribe,
    extract_audio_from_video, trim_audio,
    RECORDINGS_DIR,
)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/recordings", StaticFiles(directory=RECORDINGS_DIR), name="recordings")

# ── Google OAuth ──

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile https://www.googleapis.com/auth/drive.file",
    },
)


@app.get("/")
def root():
    return FileResponse("index.html")


# ── Auth Routes ──

@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = token["userinfo"]
    request.session["user"] = {
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture", ""),
    }
    request.session["token"] = {
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    }
    return RedirectResponse(url="/")


@app.get("/auth/me")
async def get_me(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"logged_in": False})
    return JSONResponse({"logged_in": True, **user})


@app.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


# ── Google Drive Helpers ──

def get_drive_service(request: Request):
    token_data = request.session.get("token")
    if not token_data:
        return None
    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
    )
    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, folder_name="Pass the Mic"):
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)",
    ).execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    folder = service.files().create(
        body={
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        },
        fields="id",
    ).execute()
    return folder["id"]


# ── API Routes ──

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
async def save_to_drive(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(default="Untitled"),
    mode: str = Form(default="Lyrics"),
    transcript: str = Form(...),
    speakers: str = Form(default="[]"),
):
    service = get_drive_service(request)
    if not service:
        return JSONResponse({"error": "not authenticated"}, status_code=401)

    audio_bytes = await file.read()
    folder_id = get_or_create_folder(service)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = title.strip().replace(" ", "_")[:40] if title.strip() else timestamp
    filename = f"{timestamp}_{slug}"

    # Upload audio file to Drive
    service.files().create(
        body={"name": f"{filename}.wav", "parents": [folder_id]},
        media_body=MediaInMemoryUpload(audio_bytes, mimetype="audio/wav"),
        fields="id",
    ).execute()

    # Upload transcript JSON to Drive
    meta = {
        "title": title.strip() or "Untitled",
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "transcript": transcript,
        "speakers": json.loads(speakers),
        "audio_file": f"{filename}.wav",
    }
    service.files().create(
        body={"name": f"{filename}.json", "parents": [folder_id]},
        media_body=MediaInMemoryUpload(
            json.dumps(meta, indent=2).encode(),
            mimetype="application/json",
        ),
        fields="id",
    ).execute()

    return JSONResponse({"status": "saved"})


@app.get("/sessions")
async def get_sessions(request: Request):
    service = get_drive_service(request)
    if not service:
        return JSONResponse([])

    folder_id = get_or_create_folder(service)
    results = service.files().list(
        q=f"'{folder_id}' in parents and name contains '.json' and trashed=false",
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc",
    ).execute()

    sessions = []
    for f in results.get("files", []):
        content = service.files().get_media(fileId=f["id"]).execute()
        sessions.append(json.loads(content))
    return JSONResponse(sessions)
