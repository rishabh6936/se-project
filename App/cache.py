from typing import Optional
from data import StatsResponse
import redis
import json
from typing import Optional

class Cache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.stats_key = "app:stats"
    
    def get_stats(self) -> Optional[StatsResponse]:
        """Return cached stats if available"""
        try:
            cached_data = self.redis.get(self.stats_key)
            if cached_data is None:
                return None
            stats_dict = json.loads(cached_data)
            return StatsResponse(**stats_dict)
        
        except (redis.RedisError, json.JSONDecodeError, TypeError) as e:
            print(f"Error retrieving stats from cache: {e}")
            return None
    
    def set_stats(self, stats: StatsResponse, ttl: int = 300):
        """Cache stats with TTL (default 5 minutes)"""
        try:
            if hasattr(stats, 'dict'):
                stats_json = json.dumps(stats.dict())
            elif hasattr(stats, '__dict__'):
                stats_json = json.dumps(stats.__dict__)
            else:
                stats_json = json.dumps(stats)
            
            self.redis.setex(self.stats_key, ttl, stats_json)
            
        except (redis.RedisError, json.JSONDecodeError, TypeError) as e:
            print(f"Error setting stats in cache: {e}")
    
    def clear_stats(self):
        """Clear cached stats"""
        try:
            self.redis.delete(self.stats_key)
        except redis.RedisError as e:
            print(f"Error clearing stats cache: {e}")
    
    def is_connected(self) -> bool:
        """Check if Redis connection is working"""
        try:
            self.redis.ping()
            return True
        except redis.RedisError:
            return False
