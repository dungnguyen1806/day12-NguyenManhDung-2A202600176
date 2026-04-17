# Deployment Information

## Public URL
https://lab12-final-production-17fc.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://your-agent.railway.app/health
{"status":"ok","uptime":1776435547.4333045,"instance_id":"60fde925"}
```

### API Test (with authentication)
```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
{"question":"Hello","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","user_id":"admin_user"}
```

## Environment Variables Set
- PORT: 8000
- REDIS_URL: redis://default:qWbvRGBZpCGAHkFhElzaALfdjDWPUgPk@redis.railway.internal:6379
- AGENT_API_KEY: my_super_secret_key
- LOG_LEVEL: "INFO"

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```