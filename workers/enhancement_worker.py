import pika
import json
import requests
import os
import cv2

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'video_tasks'
FASTAPI_STATUS_URL = 'http://localhost:8000/internal/video-enhancement-status'

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

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        raw_path = data.get("filepath")
        video_id = data.get("video_id")

        enhanced_output_path = raw_path.replace(".mp4", "_enhanced.mp4")
        enhance_video(raw_path, enhanced_output_path)

        requests.post(FASTAPI_STATUS_URL, json={"video_id": video_id, "enhanced_filename": os.path.basename(enhanced_output_path)})
    except Exception as err:
        print("Error:", err)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print("Enhancement Worker is ready.")
    channel.start_consuming()

if __name__ == "__main__":
    main()
