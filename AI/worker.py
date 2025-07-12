# worker.py

import os
import time
import logging
import asyncio
import sys

# --- Add project root to path for cross-folder imports ---
# This ensures that the script can find the 'Common' and 'AI' folders
# when run from within its Docker container.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Import ASYNC libraries ---
from db import Database
from queue_manager_async import AsyncRedisQueue
from model import AdvancedTopicClassifier
from rate_limiter import RedisRateLimiter # Our new rate limiter

import redis.asyncio as redis # The async redis client for the limiter

# --- Worker Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AsyncTextWorker")

# --- Environment Variables ---
MONGODB_URL = os.getenv("MONGODB_URL")
REDIS_QUEUE_URL = os.getenv("REDIS_QUEUE_URL")
REDIS_LIMITER_URL = os.getenv("REDIS_LIMITER_URL") # For our new separate limiter
QUEUE_NAME = "text_creation_queue"
DB_WRITE_LIMIT = int(os.getenv("DB_WRITE_LIMIT", "20")) # Configurable limit

# --- Initialize the AI model ONCE at startup ---
# This is a blocking operation, so we do it before the async loop starts.
logger.info("Loading AI model...")
classifier = AdvancedTopicClassifier()
logger.info("AI model loaded.")

# --- The core processing function for one job ---
async def process_job(job_data: dict, db: Database, limiter: RedisRateLimiter):
    """
    Asynchronously processes a single job: classifies text and saves it to the DB,
    respecting the rate limit.
    """
    content = job_data.get("content")
    if not content:
        logger.error(f"Invalid job data (missing 'content'): {job_data}")
        return

    try:
        # --- 1. Classify the text (CPU-bound task) ---
        # Run the synchronous, blocking classifier in a separate thread
        # to avoid freezing the main asyncio event loop.
        loop = asyncio.get_running_loop()
        logger.debug(f"Submitting classification for job {job_data.get('job_id', '')} to executor.")
        result_dict = await loop.run_in_executor(None, classifier.classify_text, content)
        topic = result_dict.get('top_topic', 'unknown')
        logger.info(f"Text classified with topic: '{topic}'")

        # --- 2. Acquire permission from the Rate Limiter ---
        # This will 'await' if the rate limit has been hit, pausing this specific
        # task without blocking other tasks.
        logger.debug(f"Acquiring DB write lock for job {job_data.get('job_id', '')}...")
        await limiter.wait_for_permission("database_writes")
        logger.info(f"Lock acquired. Writing job {job_data.get('job_id', '')} to DB.")

        # --- 3. Save the result to the database (I/O-bound task) ---
        await db.create_text_async(content=content, topic=topic)

    except Exception as e:
        logger.error(f"Failed to process job {job_data.get('job_id', '')}. Error: {e}")

# --- The main worker function ---
async def main():
    logger.info("Starting async worker process...")

    # --- Initialize ASYNC connections ---
    db_conn = Database(MONGODB_URL)
    await db_conn.connect_and_ping()

    worker_queue = AsyncRedisQueue(queue_name=QUEUE_NAME, url=REDIS_QUEUE_URL)
    await worker_queue.connect_and_ping() 
    
    
    limiter_redis_client = redis.from_url(REDIS_LIMITER_URL)
    db_rate_limiter = RedisRateLimiter(client=limiter_redis_client, limit=DB_WRITE_LIMIT, per_seconds=1)
    # We can add a ping for the limiter client too for robustness.
    
    logger.info(f"Worker is ready. Listening to queue '{QUEUE_NAME}'. Rate limit: {DB_WRITE_LIMIT}/sec.")
    
    while True:
        try:
            # --- Dequeue a job (I/O-bound task) ---
            
            job = await worker_queue.dequeue()
            if job:
                logger.info(f"Dequeued job: {job.get('job_id', 'N/A')}")
                # --- Concurrency ---
                # Start processing the job in the background without waiting for it to finish.
                # This allows the loop to immediately go back and get the next job.
                asyncio.create_task(process_job(job, db_conn, db_rate_limiter))
        except Exception as e:
            logger.error(f"Error in main worker loop: {e}. Restarting loop after 5s.")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        # This starts the asyncio event loop and runs our main function.
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker process shut down by user.")