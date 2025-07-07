import os
import time
import logging
from db import Database
from queue_manager import RedisQueue
from .model import AdvancedTopicClassifier




# --- Worker Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TextCreationWorker")

# The worker needs to connect to the same services as the main app
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
QUEUE_NAME = "text_creation_queue"

def process_job(job_data: dict, db_instance: Database):
    """
    The core logic for processing a single job.
    This is where the AI model would be called and the result saved to the DB.
    """
    content = job_data.get("content")
    topic = job_data.get("topic")

    if not content or not topic:
        logger.error(f"Invalid job data received: {job_data}")
        return

    logger.info(f"Processing text with topic '{topic}'.")
    
    #AI Model #################
    classifier = AdvancedTopicClassifier()

    # Sample texts for classification
    texts = [
        "NASA just launched a new satellite to study climate change.",
        "Taylor Swift’s concert was an amazing experience!",
        "Here's how to bake the perfect chocolate chip cookie."
    ]

    # Run inference
    for text in texts:
        result = classifier.classify_text(text)
        print("\nInput:", result["text"])
        print("Top Topic:", result["top_topic"])
        print("Confidence:", result["top_confidence"])
        print("Top Predictions:")
        for pred in result["predictions"]:
            print(f"  - {pred['topic']}: {pred['confidence']}")
    time.sleep(5) 
    
    try:
        created_text = db_instance.create_text(content=content, topic=topic)
        logger.info(f"Successfully created text with ID: {created_text.id}")
    except Exception as e:
        logger.error(f"Failed to create text in DB for job {job_data}. Error: {e}")
        # Here you might want to move the job to a "failed_jobs" queue
    
def main():
    logger.info("Starting worker process...")
    
    # Initialize connections for the worker
    db_conn = Database(MONGODB_URL)
    worker_queue = RedisQueue(queue_name=QUEUE_NAME, url=REDIS_URL)
    
    logger.info("Worker is ready and waiting for jobs.")

    while True:
        # The dequeue method will block until a job is available
        job = worker_queue.dequeue()
        if job:
            logger.info(f"Dequeued job: {job}")
            process_job(job, db_conn)
        else:
            # This part is only reached if dequeue times out (if timeout is set > 0)
            # or if there's an error.
            logger.debug("Queue is empty, waiting...")


if __name__ == "__main__":
    main()