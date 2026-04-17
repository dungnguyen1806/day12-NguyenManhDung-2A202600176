import time
import redis
from fastapi import HTTPException, Depends
from .config import settings
from .auth import verify_api_key

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def check_rate_limit(user_id: str = Depends(verify_api_key)):
    """Implement sliding window rate limiting with Redis."""
    now = time.time()
    key = f"rate_limit:{user_id}"
    
    # Remove old requests from window (60s)
    r.zremrangebyscore(key, 0, now - 60)
    
    # Count requests in window
    current_count = r.zcard(key)
    
    if current_count >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add new request
    r.zadd(key, {str(now): now})
    r.expire(key, 60)
    return user_id
