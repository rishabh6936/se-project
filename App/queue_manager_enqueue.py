import redis
import json
import logging
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisQueue:

    def __init__(self, queue_name: str, url: str):
        """
        Initialize the queue connection from a Redis URL.
        """
        self.queue_name = queue_name
        try:
            self.client = redis.from_url(url, decode_responses=True)
            self.client.ping()
            logger.info(f"Successfully connected to Redis and selected queue '{queue_name}'.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            raise

    def enqueue(self, item: dict):
        """
        Add an item to the end of the queue. The item is serialized to a JSON string.
        """
        try:
            serialized_item = json.dumps(item)
            self.client.rpush(self.queue_name, serialized_item)
            logger.info(f"Enqueued job to '{self.queue_name}'.")
        except Exception as e:
            logger.error(f"An error occurred during enqueue: {e}")
            raise
    
    def get_size(self):
        """Return the current number of items in the queue."""
        return self.client.llen(self.queue_name)