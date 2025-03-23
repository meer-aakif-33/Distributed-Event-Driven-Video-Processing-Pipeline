import pika
import json
import requests
import os
import cv2

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'video_tasks'
FASTAPI_STATUS_URL = 'http://localhost:8000/internal/metadata-extraction-status'
STORAGE_PATH = './static/storage'

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))  # <-- go up one level

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

            try:
                res = requests.post(FASTAPI_STATUS_URL, json={
                    "video_id": video_id,
                    "metadata": metadata
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

    print("[Metadata Worker is ready] Waiting for tasks...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
