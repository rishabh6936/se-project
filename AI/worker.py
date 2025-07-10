import os
import time
import logging
import os
import sys
import asyncio
import logging
import requests 
from sync_db import Database
from queue_manager_dequeue import RedisQueue
from model import AdvancedTopicClassifier




# --- Worker Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TextCreationWorker")

# The worker needs to connect to the same services as the main app
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
REDIS_URL = os.getenv("REDIS_QUEUE_URL", "redis://localhost:6379")
QUEUE_NAME = "text_creation_queue"

async def process_job(job_data: dict, db_instance: Database, classifier: AdvancedTopicClassifier):
    """
    The core logic for processing a single job.
    This is where the AI model would be called and the result saved to the DB.
    """
    content = job_data.get("content")
    topic = job_data.get("topic")

    if not content:
        logger.error(f"Invalid job data received: {job_data}")
        return

    logger.info(f"Processing text with topic '{topic}'.")

    topic = classifier.classify_text(content)
    
    try:
        created_text = await db_instance.create_text_sync(content=content, topic=topic)
        logger.info(f"Successfully created text with ID: {created_text.id}")
    except Exception as e:
        logger.error(f"Failed to create text in DB for job {job_data}. Error: {e}")
    
async def main():
    logger.info("Starting worker process...")
    
    db_conn = Database(MONGODB_URL)
    worker_queue = RedisQueue(queue_name=QUEUE_NAME, url=REDIS_URL)
    
    logger.info("Worker is ready and waiting for jobs.")
    classifier = AdvancedTopicClassifier()
    
    while True:
        job = await worker_queue.dequeue()
        if job:
            logger.info(f"Dequeued job: {job}")
            process_job(job, db_conn, classifier)
        else:
            logger.debug("Queue is empty, waiting...")


if __name__ == "__main__":
    # --- FIX 3: Use asyncio.run() to start the async main function ---
    # This creates the event loop and runs the main() coroutine until it's done.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker process shut down.")