# Video Processing Pipeline

This project is a **video processing pipeline** built with **FastAPI (backend) and React with Vite (frontend)**. Users can upload videos, process them asynchronously (metadata extraction and enhancement), and download the enhanced version. **WebSocket communication** notifies the frontend when processing is complete.


## 📁 Project Structure

```
/video-pipeline
│── server/                # Backend (FastAPI)
│   ├── main.py            # FastAPI application
│   ├── workers/           # Background workers
│   │   ├── metadata_worker.py
│   │   ├── enhancement_worker.py
│── client/                # Frontend (React with Vite)
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.jsx        # Main React application
│── requirements.txt       # Backend dependencies
│── static 
│   ├── storage           # Uploaded and Enhanced Video
│── package.json          # Frontend dependencies
```

## ✨ Features

✅ **Video Upload:** Users can upload video files via the frontend. ✅ **Metadata Extraction:** Extracts metadata asynchronously. ✅ **Video Enhancement:** Enhances video quality asynchronously. ✅ **WebSocket Communication:** Notifies the frontend when processing is complete. ✅ **Frontend UI:** React app to upload videos and view results. ✅ **FastAPI Backend:** Handles uploads, WebSocket communication, and task distribution. ✅ **RabbitMQ (Local):** Message queue for task management.

---

## 🛠 Clone the Repository

```bash
# Clone the repository
git clone https://github.com/meer-aakif-33/Distributed-Event-Driven-Video-Processing-Pipeline
cd Distributed-Event-Driven-Video-Processing-Pipeline
```
## 🏗 Setup & Installation

## Step 0 Create a python env and activate it

```
cd server
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows
```

### 1️⃣ Backend Setup

#### **Install Dependencies**

```bash
cd server
pip install -r requirements.txt
```

#### **Run RabbitMQ Locally**

Make sure RabbitMQ is installed and running:

```bash
# Start RabbitMQ service
sudo systemctl start rabbitmq-server
```

#### **Start FastAPI Server**

```bash
uvicorn main:app --reload
```

---

### 2️⃣ Worker Setup (Metadata & Enhancement)

Start two separate background workers for processing**s(open two separate terminals for two workers)**:

```bash
# Start metadata worker
cd workers
python metadata_worker.py
```

```bash
# Start enhancement worker
cd workers
python enhancement_worker.py
```

---

### 3️⃣ Frontend Setup

#### **Open new terminal and Install Dependencies**

```bash
cd client
npm install
```

#### **Run React Frontend**

```bash
npm run dev
```

---

## 🚀 Usage

1️⃣ Upload a video via the React UI. 2️⃣ The backend processes the video asynchronously. 3️⃣ WebSocket notifies the frontend when processing is complete. 4️⃣ View metadata and download the enhanced video.

---

## 📌 Tech Stack

🔹 **Backend:** FastAPI, Uvicorn, RabbitMQ, OpenCV, Python 🔹 **Frontend:** React, Vite, Tailwind CSS 🔹 **Message Queue:** RabbitMQ (Local) 🔹 **Workers:** Python (async tasks)

---
![image](https://github.com/user-attachments/assets/9515222d-b9a5-443e-a337-c9ae79826d4b)
![image](https://github.com/user-attachments/assets/eacc7be3-74f3-4b3d-b033-c3a7ca5af668)
![image](https://github.com/user-attachments/assets/697a8c19-d569-48bb-9f7b-192cf6b88359)


