from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import uuid
import os

app = FastAPI(title="YouTube → 60s MP3 API")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")


class ConvertRequest(BaseModel):
    youtube_url: str


@app.post("/convert")
def convert_youtube_to_60s_mp3(data: ConvertRequest):
    file_id = str(uuid.uuid4())

    temp_audio = f"{DOWNLOAD_DIR}/{file_id}.%(ext)s"
    final_mp3 = f"{DOWNLOAD_DIR}/{file_id}.mp3"

    # Step 1: Download best audio
    download_cmd = [
        "yt-dlp",
        "-f", "bestaudio",
        "-o", temp_audio,
        data.youtube_url
    ]

    try:
        subprocess.run(download_cmd, check=True)
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Failed to download audio")

    # Find downloaded file
    downloaded_file = None
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(file_id):
            downloaded_file = os.path.join(DOWNLOAD_DIR, f)
            break

    if not downloaded_file:
        raise HTTPException(status_code=500, detail="Downloaded file not found")

    # Step 2: Convert + trim to first 60 seconds
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", downloaded_file,
        "-t", "60",
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        final_mp3
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Failed to convert audio")

    # Cleanup temp file
    os.remove(downloaded_file)

    return {
        "file_id": file_id,
        "mp3_url": f"{PUBLIC_URL}/downloads/{file_id}.mp3",
        "duration": "60 seconds"
    }


@app.get("/downloads/{file_name}")
def download_mp3(file_name: str):
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=file_name
    )


@app.get("/")
def health_check():
    return {"status": "ok", "message": "YouTube → 60s MP3 service running"}
