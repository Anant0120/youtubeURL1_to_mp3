import uuid
import subprocess
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# ---------- CONFIG ----------
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- APP ----------
app = FastAPI(title="YouTube to MP3 API")

# Serve MP3 files publicly
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# ---------- REQUEST BODY ----------
class YouTubeRequest(BaseModel):
    youtube_url: str

# ---------- HEALTH CHECK ----------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- MAIN API ----------
@app.post("/youtube-to-mp3")
def youtube_to_mp3(payload: YouTubeRequest, request: Request):
    file_id = str(uuid.uuid4())
    output_path = f"{DOWNLOAD_DIR}/{file_id}.mp3"

    try:
        subprocess.run(
            [
                "yt-dlp",
                "-f", "bestaudio",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                payload.youtube_url,
                "-o", output_path
            ],
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail="Failed to download or convert audio")

    base_url = str(request.base_url).rstrip("/")

    return {
        "file_id": file_id,
        "mp3_url": f"{base_url}/downloads/{file_id}.mp3"
    }