#workers\metadata_worker.py

import pika
import json
import requests
import os
import cv2
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('metadata_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'video_tasks'
FASTAPI_STATUS_URL = 'http://localhost:8000/internal/metadata-extraction-status'

# Ensure absolute path to storage
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
STORAGE_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "static", "storage"))

# Ensure storage directory exists
os.makedirs(STORAGE_PATH, exist_ok=True)

def extract_metadata(video_path):
    """
    Extract video metadata with error handling.
    Returns metadata dictionary or empty dict on error.
    """
    try:
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {}

        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return {}

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        metadata = {
            "fps": round(fps, 2) if fps > 0 else 0,
            "width": width,
            "height": height,
            "duration": round(duration, 2),
            "frame_count": frame_count
        }
        
        logger.info(f"Extracted metadata: {metadata}")
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata from {video_path}: {e}")
        logger.error(traceback.format_exc())
        return {}


def callback(ch, method, properties, body):
    """
    Process RabbitMQ message with error handling.
    """
    try:
        data = json.loads(body)
        logger.info(f"Incoming message: {data}")

        raw_path = data.get("filepath")
        video_id = data.get("video_id")

        if not video_id or not raw_path:
            logger.error("Missing video_id or filepath in message")
            return

        # Get just the filename and look in storage directory
        filename = os.path.basename(raw_path)
        normalized_path = os.path.normpath(os.path.join(STORAGE_PATH, filename))

        logger.info(f"Looking for: {normalized_path}")
        logger.info(f"Current working directory: {os.getcwd()}")

        if os.path.exists(normalized_path):
            metadata = extract_metadata(normalized_path)
            
            if metadata:
                try:
                    res = requests.post(FASTAPI_STATUS_URL, json={
                        "video_id": video_id,
                        "metadata": metadata
                    }, timeout=10)
                    logger.info(f"Status update response: {res.text}")
                except Exception as e:
                    logger.error(f"Failed to notify FastAPI: {e}")
                    logger.error(traceback.format_exc())
            else:
                logger.error(f"Failed to extract metadata from {normalized_path}")
        else:
            logger.error(f"Video not found: {normalized_path}")

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from RabbitMQ message")
        logger.error(f"Raw message body: {body}")
    except Exception as err:
        logger.error(f"Error in callback: {err}")
        logger.error(f"Raw message body: {body}")
        logger.error(traceback.format_exc())


def main():
    """Main worker loop with reconnection handling."""
    while True:
        try:
            logger.info("Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, heartbeat=600))
            channel = connection.channel()
            
            # Declare exchange and queue
            exchange = channel.exchange_declare(exchange='video_tasks', exchange_type='fanout')
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue

            channel.queue_bind(exchange='video_tasks', queue=queue_name)
            channel.basic_qos(prefetch_count=1)

            logger.info("[Metadata Worker is ready] Waiting for tasks...")
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            logger.error("RabbitMQ connection failed, retrying in 5 seconds...")
            import time
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            logger.error(traceback.format_exc())
            import time
            time.sleep(5)

if __name__ == "__main__":
    main()
