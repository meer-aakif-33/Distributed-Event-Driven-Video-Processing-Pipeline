from fastapi import Request, FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiofiles
import aio_pika
import uuid
import os
import json
from datetime import datetime
from pathlib import Path

# Ensure directory exists
STORAGE_DIR = "static/storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

# App Setup
app = FastAPI()

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow frontend on localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow from frontend on localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

RABBITMQ_URL = "amqp://guest:guest@localhost/"

# In-memory store to track each video client and status
client_states = {}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[REQUEST] {request.method} {request.url}")
    response = await call_next(request)
    print(f"[RESPONSE] {request.method} {request.url} -> {response.status_code}")
    return response


@app.get("/")
def root():
    return {"message": "Server is running"}

@app.get("/video/{filename}")
def stream_video(filename: str, request: Request):
    video_path = f"static/storage/{filename}"
    if not os.path.exists(video_path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(video_path, media_type="video/mp4")

#Add Video Upload Endpoint
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    file_path = os.path.join(STORAGE_DIR, f"{video_id}_{file.filename}")
    print(f"[UPLOAD] Received file: {file.filename}")
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    client_states[video_id] = {"status": {"enhancement": False, "metadata": False}, "filename": file.filename, "filepath": file_path, "websocket": None, "metadata": None}
    await publish_to_rabbitmq({"video_id": video_id, "filepath": file_path, "filename": file.filename})
    return JSONResponse({"video_id": video_id, "message": "Video uploaded successfully"})


