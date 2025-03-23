# Commit: Initialize FastAPI Application
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