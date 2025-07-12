import redis.asyncio as redis
import json
import logging

logger = logging.getLogger(__name__)

class AsyncRedisQueue:
    """An ASYNCHRONOUS FIFO queue implemented with Redis Lists."""

    def __init__(self, queue_name: str, url: str):
        self.queue_name = queue_name
        self.client = redis.from_url(url, decode_responses=True)
        logger.info(f"AsyncRedisQueue client initialized for queue '{queue_name}'.")

    async def connect_and_ping(self):
        """Pings the Redis server to confirm a successful async connection."""
        try:
            if await self.client.ping():
                logger.info(f"Successfully connected to Redis (async) for queue '{self.queue_name}'.")
            else:
                raise ConnectionError("Redis server did not respond to ping.")
        except Exception as e:
            logger.error(f"Could not connect to Redis queue (async): {e}")
            raise

    async def dequeue(self):
        """Asynchronously removes and returns an item from the queue (blocking)."""
        try:
            result = await self.client.blpop(self.queue_name)
            if result:
                serialized_item = result[1]
                return json.loads(serialized_item)
            return None
        except Exception as e:
            logger.error(f"An error occurred during async dequeue: {e}")
            return None
    
    # You'll also want an async enqueue for your fastapi-app to use
    async def enqueue(self, item: dict):
        """Asynchronously adds an item to the end of the queue."""
        try:
            serialized_item = json.dumps(item)
            await self.client.rpush(self.queue_name, serialized_item)
        except Exception as e:
            logger.error(f"An error occurred during async enqueue: {e}")
            raise