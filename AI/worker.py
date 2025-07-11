import os
import time
import logging
import sys
import asyncio
import requests 
from db import Database
from queue_manager_dequeue import RedisQueue
from model import AdvancedTopicClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TextCreationWorker")

MONGODB_URL = os.getenv("MONGODB_URL")
REDIS_URL = os.getenv("REDIS_QUEUE_URL")
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
        created_text_id = await db_instance.create_text_async(content=content, topic=topic)
        logger.info(f"Successfully created text with ID: {created_text_id}")
    except Exception as e:
        logger.error(f"Failed to create text in DB for job {job_data}. Error: {e}")
    
async def main():
    logger.info("Starting worker process...")
    
    db_conn = Database(MONGODB_URL)
    worker_queue = RedisQueue(queue_name=QUEUE_NAME, url=REDIS_URL)
    
    logger.info("Worker is ready and waiting for jobs.")
    classifier = AdvancedTopicClassifier()
    
    while True:
        job = worker_queue.dequeue()
        if job:
            logger.info(f"Dequeued job: {job}")
            await process_job(job, db_conn, classifier)
        else:
            logger.debug("Queue is empty, waiting...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker process shut down.")