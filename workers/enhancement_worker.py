#workers\enhancement_worker.py

import pika
import json
import requests
import os
import cv2
import logging
import traceback
from datetime import datetime

# Try importing imageio as a fallback
try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    logging.warning("imageio not available - will use OpenCV fallback only")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('enhancement_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'video_tasks'
FASTAPI_STATUS_URL = 'http://localhost:8000/internal/video-enhancement-status'
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
STORAGE_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "static", "storage"))

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2

def enhance_video(video_path, output_path):
    """
    Enhance video with brightness and contrast adjustments.
    Tries imageio first, then falls back to OpenCV with multiple codecs.
    """
    try:
        # Check if output directory exists and create if needed
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            logger.info(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return False

        original_fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        new_fps = 15.0

        if original_fps == 0 or width == 0 or height == 0:
            logger.error(f"Invalid video properties: fps={original_fps}, width={width}, height={height}")
            cap.release()
            return False

        logger.info(f"Input video: {width}x{height} @ {original_fps} fps")

        # METHOD 1: Try imageio (best Windows support)
        if IMAGEIO_AVAILABLE:
            logger.info("Method 1: Trying imageio...")
            try:
                frames = []
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Validate and enhance frame
                    if frame.shape[0] != height or frame.shape[1] != width:
                        frame = cv2.resize(frame, (width, height))
                    
                    # Ensure BGR 3-channel
                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    elif frame.shape[2] == 4:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    
                    # Enhance
                    enhanced = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                    # Convert BGR to RGB for imageio
                    enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
                    frames.append(enhanced_rgb)
                    frame_count += 1
                
                if frames:
                    # Use MP4 for better compatibility
                    output_mp4 = output_path.replace('.avi', '.mp4')
                    logger.info(f"Saving {len(frames)} frames to {output_mp4} using imageio...")
                    imageio.mimsave(output_mp4, frames, fps=new_fps)
                    cap.release()
                    logger.info(f"Successfully saved video with imageio: {len(frames)} frames")
                    return True
            except Exception as e:
                logger.warning(f"imageio failed: {e}")

        # METHOD 2: Try OpenCV codecs
        logger.info("Method 2: Trying OpenCV codecs...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        for codec in ['MJPG', 'XVID', 'DIVX', 'FFV1']:
            try:
                logger.info(f"Trying codec: {codec}")
                fourcc = cv2.VideoWriter_fourcc(*codec)
                out = cv2.VideoWriter(output_path, fourcc, new_fps, (width, height))
                
                if not out.isOpened():
                    logger.warning(f"{codec} failed to open")
                    continue
                
                written = 0
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    if frame.shape[0] != height or frame.shape[1] != width:
                        frame = cv2.resize(frame, (width, height))
                    
                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    elif frame.shape[2] != 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    
                    enhanced = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                    
                    if out.write(enhanced):
                        written += 1
                
                out.release()
                
                if written > 0:
                    cap.release()
                    logger.info(f"Successfully saved {written} frames with {codec}")
                    return True
                
            except Exception as e:
                logger.warning(f"{codec} error: {e}")
                continue
        
        cap.release()
        logger.error("All methods failed to save video")
        return False
        
    except Exception as e:
        logger.error(f"Error in enhance_video: {e}")
        logger.error(traceback.format_exc())
        return False


def extract_metadata(video_path):
    """Extract video metadata safely with error handling."""
    try:
        cap = cv2.VideoCapture(video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            "fps": round(fps, 2),
            "width": width,
            "height": height,
            "duration": round(duration, 2),
            "frame_count": frame_count
        }
    except Exception as e:
        logger.error(f"Error extracting metadata from {video_path}: {e}")
        return {}


def callback(ch, method, properties, body):
    """Process RabbitMQ message with error handling and retries."""
    try:
        data = json.loads(body)
        logger.info(f"Incoming message: {data}")

        raw_path = data.get("filepath")
        video_id = data.get("video_id")

        if not video_id or not raw_path:
            logger.error("Missing video_id or filepath in message")
            return

        normalized_path = os.path.normpath(os.path.join(PROJECT_ROOT, raw_path))
        logger.info(f"Looking for: {normalized_path}")
        logger.info(f"Current working directory: {os.getcwd()}")

        if not os.path.exists(normalized_path):
            logger.error(f"Video not found: {normalized_path}")
            return

        try:
            # Extract metadata from original
            metadata = extract_metadata(normalized_path)
            logger.info(f"Original metadata: {metadata}")
            
            # Create output path - use AVI format which has better codec support on Windows
            enhanced_filename = os.path.basename(normalized_path).replace(".mp4", "_enhanced.mp4")
            enhanced_output_path = os.path.join(os.path.dirname(normalized_path), enhanced_filename)

            # Enhance the video
            logger.info(f"Starting enhancement for {video_id}")
            success = enhance_video(normalized_path, enhanced_output_path)
            
            if not success:
                logger.error(f"Video enhancement failed for {video_id}")
                # Notify backend of failure
                try:
                    requests.post(FASTAPI_STATUS_URL, json={
                        "video_id": video_id,
                        "metadata": {},
                        "enhanced_filename": enhanced_filename,
                        "error": "Enhancement failed - codec unavailable"
                    }, timeout=5)
                except Exception as e:
                    logger.error(f"Failed to notify FastAPI of failure: {e}")
                return

            # Extract metadata from enhanced video
            enhanced_metadata = extract_metadata(enhanced_output_path)
            logger.info(f"Enhanced metadata: {enhanced_metadata}")
            logger.info(f"Enhancement complete - Saved to: {enhanced_output_path}")

            # Notify FastAPI backend
            try:
                res = requests.post(FASTAPI_STATUS_URL, json={
                    "video_id": video_id,
                    "metadata": enhanced_metadata,
                    "enhanced_filename": enhanced_filename
                }, timeout=10)
                logger.info(f"Status update response: {res.text}")
            except Exception as e:
                logger.error(f"Failed to notify FastAPI: {e}")
                logger.error(traceback.format_exc())

        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            logger.error(traceback.format_exc())

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

            logger.info("[Enhancement Worker is ready] Waiting for tasks...")
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
