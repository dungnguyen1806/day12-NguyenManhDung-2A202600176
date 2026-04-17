# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcoded API Keys/Secrets:** `OPENAI_API_KEY` is written directly in the source code, risking leaks if pushed to VCS.
2. **Hardcoded Debug Mode (Poor Config Management):** `DEBUG = True` is hardcoded, which is dangerous in production as it can leak sensitive information.
3. **Poor Logging:** Uses `print()` instead of structured logging, making it difficult to analyze logs in production.
4. **Lack of Health Checks:** No `/health` or `/ready` endpoints, so orchestrators can't monitor the app's status.
5. **Fixed Port and Host:** Port `8000` and host `localhost` are hardcoded, making it incompatible with cloud environments that inject `PORT` and require `0.0.0.0` binding.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded in code | Environment variables | Allows changing settings without code changes; keeps secrets out of Git. |
| Health check | None | `/health` & `/ready` | Essential for cloud platforms to monitor service health and route traffic. |
| Logging | `print()` | Structured JSON logging | Enables automated log analysis and better debugging in distributed systems. |
| Shutdown | Abrupt | Graceful (SIGTERM) | Ensures requests are completed before the service stops, preventing data loss. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** `python:3.11`.
2. **Working directory:** `/app` (set using the `WORKDIR` instruction).
3. **Why COPY requirements.txt first?** To leverage Docker layer caching. By copying only the dependencies list first and installing them, Docker caches the installation layer. If source code changes but the requirements don't, Docker skips the expensive `pip install` step.
4. **CMD vs ENTRYPOINT differences:**
   - `CMD` provides default arguments for the container and can be easily overridden during `docker run`.
   - `ENTRYPOINT` configures the container to run as an executable. Arguments passed to `docker run` are appended to the entrypoint, and it is harder to override.

### Exercise 2.2: Build and run
- **Image size (Develop):** 1.67 GB

### Exercise 2.3: Image size comparison
- **Develop:** 1.67 GB
- **Production:** 262 MB
- **Difference:** ~84.3% reduction

**Why is the production image smaller?**
- **Multi-stage build:** The `builder` stage handles dependency installation (including build tools), while the `runtime` stage only copies the final installed packages and application code.
- **Base Image:** The development version likely uses a full `python:3.11` image (~1GB), whereas the production version uses a slim or alpine-based image for the runtime stage.
- **No Build Cache/Tools:** Production images exclude `pip` cache, compilers, and header files required only during the build process.

### Exercise 2.4: Docker Compose stack
**Services started:**
1. **agent:** The FastAPI AI agent application.
2. **redis:** Used for session caching and rate limiting.
3. **qdrant:** A vector database used for RAG (Retrieval-Augmented Generation).
4. **nginx:** Acts as a reverse proxy and load balancer, exposing the application to the outside world.

**Communication:**
- **External to Internal:** Only Nginx exposes ports (80/443) to the host. All external traffic enters through Nginx.
- **Load Balancing:** Nginx forwards requests to the `agent` service instances.
- **Service Discovery:** All services are connected to the `internal` bridge network. They communicate using service names as hostnames (e.g., the agent connects to `redis:6379` and `http://qdrant:6333`).
- **Dependencies:** The `agent` service waits for `redis` and `qdrant` to be healthy before starting.

**Architecture Diagram:**
```text
[ Client ]
    | (HTTP/HTTPS: Port 80/443)
    v
[ Nginx (Reverse Proxy) ]
    | (Internal Network)
    +-------------------> [ Agent (FastAPI) ]
                                |
                                +-----> [ Redis (Cache/Rate Limit) ]
                                |
                                +-----> [ Qdrant (Vector DB) ]
```


## Part 3: Cloud Deployment

### Exercise 3.1:
Screenshot: folder screenshot
Link: https://ai26-production.up.railway.app

### Exercise 3.2:
Screenshot: folder screenshot
Link: https://ai-agent-evfd.onrender.com

## Part 4: API Security

### Exercise 4.1: API Key authentication
- **Where is the API key checked?** It is checked in the `verify_api_key` function, which is used as a FastAPI dependency (`Depends(verify_api_key)`) for the `/ask` endpoint.
- **What happens if the key is wrong?** The server returns a `403 Forbidden` error with the detail `"Invalid API key."`. If the `X-API-Key` header is missing entirely, it returns a `401 Unauthorized` error.
- **How to rotate the key?** Change the `AGENT_API_KEY` environment variable and restart the application.

**Test Observations:**
- Sending `secret-key-123` resulted in `403 Invalid API key`.
- Sending `demo-key-change-in-production` (the default) resulted in a successful response.
- *Note:* The code currently expects `question` as a query parameter (e.g., `/ask?question=Hello`) rather than in the JSON body, which caused a 422 error in the initial JSON body test.

### Exercise 4.2: JWT authentication (Advanced)

curl -X POST http://localhost:8000/auth/token -H "Content-Type: application/json" -d '{"username": "student", "password": "demo123"}'                         
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0MjIxMzEsImV4cCI6MTc3NjQyNTczMX0.OObIXjF3gI-5qxkt8yjw8uYcwDNwLjaKWsFq4UAQF0w","token_type":"bearer","expires_in_minutes":60,"hint":"Include in header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."}%                                      

curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0MjIxMzEsImV4cCI6MTc3NjQyNTczMX0.OObIXjF3gI-5qxkt8yjw8uYcwDNwLjaKWsFq4UAQF0w" -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "what is docker?"}'
{"question":"what is docker?","answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!","usage":{"requests_remaining":9,"budget_remaining_usd":1.9e-05}}%                         

### Exercise 4.3: Rate limiting
- **Algorithm used:** Sliding Window Counter (implemented using a `deque` of timestamps).
- **Limit:** 10 requests per minute for regular users (`rate_limiter_user`).
- **How to bypass limit for admin:** The system uses Role-Based Access Control (RBAC). In `app.py`, the `ask_agent` endpoint checks the user's role from the JWT token. If the role is `"admin"`, it switches to `rate_limiter_admin`, which has a much higher limit of 100 requests per minute.

**Test Observations:**
```text
{"question":"Test 1","answer":"...","usage":{"requests_remaining":9,...}}
...
{"question":"Test 10","answer":"...","usage":{"requests_remaining":0,...}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}
```
The test confirms that after 10 requests within a minute, the server returns a `429 Too Many Requests` error with a `retry_after_seconds` hint.


## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks
- **Health endpoint (/health):** Acts as a **Liveness Probe**. It returns the overall status of the application, uptime, and basic checks (like memory usage). If this returns a non-200 status, orchestrators like Docker or Kubernetes will restart the container.
- **Ready endpoint (/ready):** Acts as a **Readiness Probe**. It checks if the application is fully started and all its dependencies (like Redis) are available. Load balancers use this to decide whether to route traffic to this specific instance.

### Exercise 5.2: Graceful shutdown
- **How it works:** When a container receives a `SIGTERM` signal (e.g., during a deployment or scaling down), the application stops accepting new requests and waits for in-flight requests to complete before exiting.
- **Implementation:** Uses a FastAPI `lifespan` context manager to set `_is_ready = False` (so the readiness probe fails and no new traffic is sent) and then waits for the `_in_flight_requests` counter to reach zero (with a timeout).

### Exercise 5.3: Stateless design
- **Statelessness:** The agent does not store any conversation history or session data in its local memory. Instead, it uses **Redis** as a centralized state store.
- **Why it is important for scaling:** In a multi-instance setup, a user's requests might be routed to different instances (e.g., Request 1 to Instance A, Request 2 to Instance B). If the state were stored in memory, Instance B wouldn't know about the conversation history from Instance A. By using Redis, all instances can access the same session data.

### Exercise 5.4: Load balancing
- **Nginx's role:** Nginx acts as a reverse proxy and load balancer. It exposes a single entry point (port 8080) and distributes incoming HTTP requests among multiple agent instances (scaled to 3 in the demo).
- **Observation:** In the response from the `/chat` endpoint, the `served_by` field changes between requests (e.g., `instance-abc`, `instance-xyz`), proving that different instances are handling the traffic. However, the `session_id` and conversation history remain consistent because they are retrieved from Redis.

### Exercise 5.5: Test stateless
Running the `test_stateless.py` script simulates a real-world scenario where instances might be restarted or replaced. Even if an instance is "killed" between turns, the conversation history is preserved because it's stored in Redis, and the new instance can pick up right where the old one left off.


