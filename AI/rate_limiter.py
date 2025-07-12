# Common/rate_limiter.py

import redis.asyncio as redis
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    """
    An asynchronous Token Bucket style rate limiter using Redis.
    Designed to be shared by multiple distributed asyncio workers.
    """
    def __init__(self, client: redis.Redis, limit: int, per_seconds: int = 1, prefix: str = "rate_limit"):
        """
        Initializes the rate limiter.

        Args:
            client: An active async Redis client instance from redis.asyncio.
            limit: The maximum number of actions allowed per time window.
            per_seconds: The duration of the time window in seconds. Defaults to 1.
            prefix: A prefix for Redis keys to avoid name collisions.
        """
        if not isinstance(client, redis.Redis):
            raise TypeError("The 'client' must be an instance of redis.asyncio.Redis")
        
        self.client = client
        self.limit = limit
        self.per_seconds = per_seconds
        self.key_prefix = prefix

    def _get_current_window(self) -> int:
        """Calculates the current time window's timestamp."""
        return int(time.time() / self.per_seconds)

    async def _acquire_token(self, identifier: str) -> bool:
        """
        Tries to acquire a single token for a given identifier. This is the core
        atomic operation. Returns True if the request is within the limit, False otherwise.
        """
        # Create a unique key for the current time window (e.g., 'rate_limit:db_writes:1678886400')
        window = self._get_current_window()
        key = f"{self.key_prefix}:{identifier}:{window}"
        
        # Atomically increment the counter for the current window
        current_count = await self.client.incr(key)
        
        # If this is the first token for this window, set an expiry on the key.
        # This is a self-cleaning mechanism so old keys don't clutter Redis.
        if current_count == 1:
            # Expire the key slightly after the window ends to handle edge cases.
            await self.client.expire(key, self.per_seconds + 5)
            
        # Check if the current count has exceeded the defined limit
        if current_count > self.limit:
            return False
        
        return True

    async def wait_for_permission(self, identifier: str, max_wait_seconds: int = 10):
        """
        Asynchronously waits until permission is granted by the rate limiter.
        This is the main method that workers should call.

        Args:
            identifier (str): A name for the action being limited (e.g., 'database_writes').
            max_wait_seconds (int): The maximum time to wait before raising a TimeoutError.

        Raises:
            TimeoutError: If a token cannot be acquired within the specified wait time.
        """
        start_time = time.time()
        while True:
            # Attempt to acquire a token
            if await self._acquire_token(identifier):
                # Success! Permission granted. Exit the loop.
                return
            
            # If we failed, check if we've been waiting too long
            if time.time() - start_time > max_wait_seconds:
                raise TimeoutError(
                    f"Could not acquire permission for '{identifier}' within {max_wait_seconds} seconds."
                )

            # Wait asynchronously before the next attempt.
            # Using asyncio.sleep is crucial as it doesn't block the entire event loop.
            sleep_duration = 0.1
            logger.debug(f"Rate limit for '{identifier}' reached. Awaiting {sleep_duration}s...")
            await asyncio.sleep(sleep_duration)


