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
Screenshot: folder Screenshot
Link: https://ai26-production.up.railway.app

