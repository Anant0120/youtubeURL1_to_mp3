from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import uuid
import os

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class ConvertRequest(BaseModel):
    youtube_url: str

@app.post("/convert")
def convert_youtube_to_mp3(data: ConvertRequest):
    file_id = str(uuid.uuid4())
    output_path = f"{DOWNLOAD_DIR}/{file_id}.mp3"

    command = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "-o", output_path,
        data.youtube_url
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Failed to convert video")

    public_url = os.getenv("PUBLIC_URL")
    if not public_url:
        raise HTTPException(status_code=500, detail="PUBLIC_URL not set")

    return {
        "mp3_url": f"{public_url}/downloads/{file_id}.mp3"
    }

@app.get("/downloads/{file_name}")
def download_file(file_name: str):
    file_path = f"{DOWNLOAD_DIR}/{file_name}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/mpeg")
