import pika
import json
import requests
import os
import cv2

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'video_tasks'
FASTAPI_STATUS_URL = 'http://localhost:8000/internal/video-enhancement-status'
# STORAGE_PATH = './static/storage'  # corrected to match FastAPI

def enhance_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 24
    width = int(cap.get(3))
    height = int(cap.get(4))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        enhanced_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
        out.write(enhanced_frame)

    cap.release()
    out.release()

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))  # <-- go up one level
STORAGE_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "static", "storage"))

def extract_metadata(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps else 0
    cap.release()
    return {
        "fps": round(fps, 2),
        "width": width,
        "height": height,
        "duration": round(duration, 2),
        "frame_count": frame_count
    }


def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        print(f"[Incoming message] {data}")

        raw_path = data.get("filepath")
        video_id = data.get("video_id")

        normalized_path = os.path.normpath(os.path.join(PROJECT_ROOT, raw_path))
        
        print(f"[Looking for] {normalized_path}")
        print(f"[Current working directory] {os.getcwd()}")

        if os.path.exists(normalized_path):
            metadata = extract_metadata(normalized_path)
            # Create output path for enhanced video
            enhanced_output_path = normalized_path.replace(".mp4", "_enhanced.mp4")
            enhanced_filename = os.path.basename(enhanced_output_path)

            # Actually enhance the video
            enhance_video(normalized_path, enhanced_output_path)

            print(f"[Enhancement complete] Saved to: {enhanced_output_path}")

            try:
                res = requests.post(FASTAPI_STATUS_URL, json={
                    "video_id": video_id,
                    "metadata": metadata,
                    "enhanced_filename": enhanced_filename
                })
                print("Metadata sent:", res.text)
            except Exception as e:
                print("Failed to notify FastAPI:", e)
        else:
            print(f"[Video not found] Path: {normalized_path}")

    except Exception as err:
        print("Error while handling task:", err)
        print("Raw message body:", body)


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    exchange = channel.exchange_declare(exchange='video_tasks', exchange_type='fanout')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='video_tasks', queue=queue_name)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print("[Enhancement Worker is ready] Waiting for tasks...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
