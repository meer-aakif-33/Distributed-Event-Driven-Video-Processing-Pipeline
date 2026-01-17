from fastapi import Request, FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import aiofiles
import aio_pika
import uuid
import os
import json
from datetime import datetime
from pathlib import Path


# Ensure directory exists
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../static/storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# App Setup
app = FastAPI()

client_states = {}

# Get the absolute path of the project root (where "server" is located)
project_root = os.path.dirname(os.path.abspath(__file__))  # This points to 'server'
static_dir = os.path.join(project_root, "..", "static")  # Moves one level up

# Ensure the static folder exists
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount the static directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Allow frontend on localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                    "http://localhost:5174",
                    "http://localhost:5175"],  # Allow from frontend on localhost   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

RABBITMQ_URL = "amqp://guest:guest@localhost/"

# In-memory store to track each video client and status
client_states = {}

# Global request logger middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[REQUEST] {request.method} {request.url}")
    response = await call_next(request)
    print(f"[RESPONSE] {request.method} {request.url} -> {response.status_code}")
    return response

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    file_path = os.path.join(STORAGE_DIR, f"{video_id}_{file.filename}")

    print(f"[UPLOAD] Received file: {file.filename}")
    print(f"[UPLOAD] Attempting to save file: {file_path}")

    # Save uploaded file
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
        print(f"[DEBUG] File successfully saved at: {file_path}")
    except Exception as e:
        print(f"[ERROR][UPLOAD] Failed to handle upload: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

    # Initialize client state
    client_states[video_id] = {
        "status": {"enhancement": False, "metadata": False},
        "filename": file.filename,
        "filepath": file_path,
        "websocket": None,
        "metadata": None,
    }
    print(f"[UPLOAD] Client state initialized for {video_id}: {client_states[video_id]}")

    # Publish task to RabbitMQ
    await publish_to_rabbitmq({
        "video_id": video_id,
        "filepath": file_path,
        "filename": file.filename,
    })
    print(f"[UPLOAD] Published task to RabbitMQ: {video_id}")

    return JSONResponse({"video_id": video_id, "message": "Video uploaded successfully"})

async def publish_to_rabbitmq(payload: dict):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        exchange = await channel.declare_exchange("video_tasks", aio_pika.ExchangeType.FANOUT)
        message = aio_pika.Message(body=json.dumps(payload).encode())
        await exchange.publish(message, routing_key="")
        await connection.close()
        print(f"[DEBUG] Published task to RabbitMQ: {payload}")
    except Exception as e:
        print(f"[ERROR] RabbitMQ publish failed. Ensure RabbitMQ is running. Details: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, video_id: str):
    print("[INIT] /ws route loaded.")
    print(f"[WS] WebSocket request for video_id: {video_id}")
    await websocket.accept()

    if video_id not in client_states:
        print(f"[WS][ERROR] Invalid video_id: {video_id}")
        await websocket.send_json({"error": "Invalid video_id"})
        await websocket.close()
        return

    # Store the WebSocket
    client_states[video_id]["websocket"] = websocket
    await websocket.send_json({"message": "WebSocket connected."})
    print(f"[WS] WebSocket accepted for video_id: {video_id}")

    # Check if processing is already done
    status = client_states[video_id]["status"]
    if status["enhancement"] and status["metadata"]:
        await maybe_notify_client(video_id)

    try:
        while True:
            await websocket.receive_text()  # Keep alive
            print(f"[WS] Received keep-alive ping from {video_id}")
    except WebSocketDisconnect:
        print(f"[WS] WebSocket disconnected for video_id: {video_id}")
        client_states[video_id]["websocket"] = None


async def maybe_notify_client(video_id: str):
    state = client_states.get(video_id)

    print(f"[MAYBE_NOTIFY] Checking readiness for {video_id}")
    if not state:
        print("[ERROR] No state found for video_id!")
        return
    
    print(f"[DEBUG] Current processing status: {json.dumps(state['status'])}")

    if state["status"]["enhancement"] and state["status"]["metadata"]:
        ws = state.get("websocket")
        if ws:
            try:
                print(f"[MAYBE_NOTIFY] Sending WebSocket message for {video_id}")
                await ws.send_json({
                    "message": "Processing complete!",
                    "video_id": video_id,
                    "metadata": {
                        "enhancement": state.get("enhancement_metadata", {}),
                        "metadata_extraction": state.get("metadata", {}),
                    },
                    "enhanced_video_url": f"http://localhost:8000/stream/{state['enhanced_filename']}"
                })
                print(f"[MAYBE_NOTIFY] Notification sent for {video_id}")
            except Exception as e:
                print(f"[ERROR] Error sending WebSocket message for {video_id}: {e}")
        else:
            print(f"[MAYBE_NOTIFY] No WebSocket connected for {video_id}")
    else:
        print(f"[MAYBE_NOTIFY] Processing still incomplete for {video_id}")

@app.post("/internal/video-enhancement-status")
async def enhancement_status_update(request: Request):
    data = await request.json()
    video_id = data.get("video_id")
    metadata = data.get("metadata", {})
    enhanced_filename = data.get("enhanced_filename")

    print(f"[ENHANCEMENT] Received enhancement update for video_id: {video_id}")
    print("[DEBUG] Current client_states:", client_states)
    if video_id not in client_states:
        return JSONResponse({"error": "Invalid video_id"}, status_code=400)

    client_states[video_id]["status"]["enhancement"] = True
    client_states[video_id]["enhancement_metadata"] = metadata
    client_states[video_id]["enhanced_filename"] = enhanced_filename

    await maybe_notify_client(video_id)
    return {"message": "Enhancement status updated."}

@app.post("/internal/metadata-extraction-status")
async def metadata_status_update(request: Request):
    data = await request.json()
    video_id = data.get("video_id")
    metadata = data.get("metadata", {})

    print(f"[METADATA] Received metadata update for video_id: {video_id}")

    if video_id not in client_states:
        return JSONResponse({"error": "Invalid video_id"}, status_code=400)

    client_states[video_id]["status"]["metadata"] = True
    client_states[video_id]["metadata"] = metadata

    await maybe_notify_client(video_id)
    return {"message": "Metadata status updated."}

@app.get("/download/{filename}")
async def download_video(filename: str):
    video_path = os.path.join(STORAGE_DIR, filename)
    print(f"[DOWNLOAD] Requested: {filename}")
    print(f"[DOWNLOAD] Resolved path: {video_path}")
    if not os.path.exists(video_path):
        print("[ERROR] File not found.")
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/stream/{filename}")
async def stream_video(request: Request, filename: str):
    """Stream video with full range request support for seeking"""
    video_path = os.path.join(STORAGE_DIR, filename)
    
    print(f"[STREAM] Requested: {filename}")
    print(f"[STREAM] Resolved path: {video_path}")
    
    if not os.path.exists(video_path):
        print("[ERROR] File not found.")
        raise HTTPException(status_code=404, detail="File not found")
    
    file_size = os.path.getsize(video_path)
    
    # Handle range requests
    range_header = request.headers.get("range")
    
    if range_header:
        # Parse range header (e.g., "bytes=0-1023")
        try:
            range_value = range_header.replace("bytes=", "")
            start, end = range_value.split("-")
            start = int(start)
            end = int(end) if end else file_size - 1
            
            if start > end or start >= file_size or end >= file_size:
                raise ValueError("Invalid range")
            
            content_length = end - start + 1
            
            print(f"[STREAM] Range request: bytes {start}-{end}/{file_size}")
            
            async def range_stream():
                async with aiofiles.open(video_path, "rb") as f:
                    await f.seek(start)
                    bytes_remaining = content_length
                    chunk_size = 1024 * 256  # 256KB chunks
                    while bytes_remaining > 0:
                        read_size = min(chunk_size, bytes_remaining)
                        chunk = await f.read(read_size)
                        if not chunk:
                            break
                        yield chunk
                        bytes_remaining -= len(chunk)
            
            return StreamingResponse(
                range_stream(),
                status_code=206,
                media_type="video/mp4",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(content_length),
                    "Accept-Ranges": "bytes",
                    "Content-Type": "video/mp4",
                    "Cache-Control": "no-cache",
                }
            )
        except (ValueError, IndexError):
            print("[STREAM] Invalid range request, serving full file")
    
    # Serve full file
    print(f"[STREAM] Serving full file: {file_size} bytes")
    return FileResponse(
        video_path,
        media_type="video/mp4",
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        }
    )

@app.get("/video/{filename}")
async def stream_video_legacy(request: Request, filename: str):
    """Legacy endpoint - redirects to new /stream endpoint"""
    return await stream_video(request, filename)

@app.get("/status/{video_id}")
async def get_processing_status(video_id: str):
    """Get real-time processing status for a video"""
    if video_id not in client_states:
        return JSONResponse({"error": "Invalid video_id"}, status_code=404)
    
    state = client_states[video_id]
    return {
        "video_id": video_id,
        "filename": state.get("filename"),
        "status": state.get("status", {}),
        "enhancement_metadata": state.get("enhancement_metadata", {}),
        "metadata": state.get("metadata", {}),
        "enhanced_filename": state.get("enhanced_filename"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_processing": len([v for v in client_states.values() if not v["status"]["enhancement"] or not v["status"]["metadata"]])
    }
