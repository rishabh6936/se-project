import redis
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisQueue:
    """A simple FIFO queue implemented with Redis Lists."""

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
            
    def dequeue(self, block: bool = True, timeout: int = 0):
        """
        Remove and return an item from the front of the queue (blocking by default).
        """
        try:
            result = self.client.blpop(self.queue_name, timeout=timeout)
            if result:
                serialized_item = result[1]
                return json.loads(serialized_item)
            return None
        except Exception as e:
            logger.error(f"An error occurred during dequeue: {e}")
            return None

    def get_size(self):
        """Return the current number of items in the queue."""
        return self.client.llen(self.queue_name)