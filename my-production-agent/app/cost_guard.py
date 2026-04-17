import redis
from datetime import datetime
from fastapi import HTTPException, Depends
from .config import settings
from .rate_limiter import check_rate_limit

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def check_budget(user_id: str = Depends(check_rate_limit)):
    """Check monthly budget using Redis."""
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current_cost = float(r.get(key) or 0)
    
    if current_cost >= settings.MONTHLY_BUDGET_USD:
        raise HTTPException(status_code=402, detail="Monthly budget exceeded")
    
    # Simulating cost increment per request ($0.01)
    r.incrbyfloat(key, 0.01)
    r.expire(key, 32 * 24 * 3600)  # 32 days TTL
    return user_id
