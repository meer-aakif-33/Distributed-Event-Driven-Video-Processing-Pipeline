import pika
import json
import requests
import os
import cv2

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'video_tasks'
FASTAPI_STATUS_URL = 'http://localhost:8000/internal/metadata-extraction-status'

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
        raw_path = data.get("filepath")
        video_id = data.get("video_id")

        if os.path.exists(raw_path):
            metadata = extract_metadata(raw_path)
            requests.post(FASTAPI_STATUS_URL, json={"video_id": video_id, "metadata": metadata})
    except Exception as err:
        print("Error:", err)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print("Metadata Worker is ready.")
    channel.start_consuming()

if __name__ == "__main__":
    main()
