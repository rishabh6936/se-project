import redis
import json
import logging
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisQueue:
    """A simple FIFO queue implemented with Redis Lists."""

    def __init__(self, queue_name: str, url: str):
        """
        Initialize the queue connection from a Redis URL.
        :param queue_name: The name of the queue (Redis key).
        :param url: The Redis connection URL (e.g., 'redis://localhost:6379').
        """
        self.queue_name = queue_name
        try:
            # from_url is a convenient way to connect using a standard URL string
            self.client = redis.from_url(url, decode_responses=True)
            self.client.ping()
            logger.info(f"Successfully connected to Redis and selected queue '{queue_name}'.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            raise

    def enqueue(self, item: dict):
        """
        Add an item to the end of the queue. The item is serialized to a JSON string.
        :param item: The dictionary to add to the queue.
        """
        try:
            serialized_item = json.dumps(item)
            self.client.rpush(self.queue_name, serialized_item)
            logger.info(f"Enqueued job to '{self.queue_name}'.")
        except Exception as e:
            logger.error(f"An error occurred during enqueue: {e}")
            raise

    def dequeue(self, block: bool = True, timeout: int = 0):
        """
        Remove and return an item from the front of the queue (blocking by default).
        :param block: Whether to block until an item is available.
        :param timeout: Timeout in seconds for blocking. 0 means block indefinitely.
        :return: The deserialized item as a dict, or None if timeout occurs.
        """
        try:
            # BLPOP is a blocking pop. It returns a tuple (queue_name, item)
            # A timeout of 0 means it will wait forever.
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