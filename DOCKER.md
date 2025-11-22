# 🐳 Docker Setup Guide for JobSathi

This guide explains how to run JobSathi using Docker and Docker Compose.

## Prerequisites

- **Docker** 20.10 or higher
- **Docker Compose** 2.0 or higher
- At least 4GB of free RAM (for ASR model loading)
- 10GB of free disk space

### Install Docker

#### Windows
Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)

#### Linux (Ubuntu/Debian)
```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### macOS
Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)

## Quick Start with Docker

### 1. Configure Environment Variables

Copy the example environment files and add your API keys:

```bash
# Backend environment
cp backend/.env.example backend/.env

# Edit backend/.env and add your API keys
# - GEMINI_API_KEY (required)
# - ADZUNA_APP_ID and ADZUNA_APP_KEY (optional)
# - JOOBLE_KEY (optional)
# - SERPAPI_KEY (optional)

# Frontend environment (usually no changes needed)
cp frontend/.env.example frontend/.env
```

### 2. Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clears cached models)
docker-compose down -v
```

## Docker Commands Reference

### Development Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a specific service
docker-compose restart backend

# Rebuild a specific service
docker-compose up -d --build backend

# Execute command in running container
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Debugging

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Inspect containers
docker-compose logs backend --tail=100
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove all unused containers, networks, images
docker system prune -a

# Remove volumes (WARNING: deletes model cache)
docker volume prune
```

## Docker Architecture

```
jobsathi/
├── docker-compose.yml       # Orchestration configuration
├── Dockerfile               # Backend image
├── .dockerignore           # Files to exclude from builds
├── backend/
│   ├── .env                # Backend environment variables
│   ├── .env.example        # Backend env template
│   └── app/
│       ├── Dockerfile      # (not used, using root Dockerfile)
│       └── database/       # Mounted volume for persistence
├── frontend/
│   ├── Dockerfile          # Frontend image
│   ├── .dockerignore       # Frontend build exclusions
│   ├── .env                # Frontend environment variables
│   └── .env.example        # Frontend env template
```

## Service Configuration

### Backend Service
- **Base Image**: python:3.10-slim
- **Port**: 8000
- **Volumes**: 
  - `./backend/app:/app` - Code hot-reload
  - `./backend/app/database:/app/database` - Data persistence
  - `model_cache:/root/.cache/huggingface` - Model caching
- **Environment**: Loaded from `backend/.env`
- **Health Check**: HTTP GET to `/health` endpoint

### Frontend Service
- **Base Image**: node:18-alpine
- **Port**: 5173
- **Volumes**: 
  - `./frontend:/app` - Code hot-reload
  - `/app/node_modules` - Anonymous volume for dependencies
- **Environment**: Loaded from `frontend/.env`
- **Depends On**: Backend service (waits for health check)

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ Yes | - |
| `ADZUNA_APP_ID` | Adzuna job search app ID | ⚠️ Optional | - |
| `ADZUNA_APP_KEY` | Adzuna job search app key | ⚠️ Optional | - |
| `JOOBLE_KEY` | Jooble job search API key | ⚠️ Optional | - |
| `SERPAPI_KEY` | SerpAPI key for Google Jobs | ⚠️ Optional | - |
| `HOST` | Server host | ❌ No | 0.0.0.0 |
| `PORT` | Server port | ❌ No | 8000 |
| `ASR_MODEL_ID` | Hugging Face model ID | ❌ No | ai4bharat/indic-conformer-600m-multilingual |
| `DEVICE` | Processing device (auto/cpu/cuda) | ❌ No | auto |

### Frontend (`frontend/.env`)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_BASE_URL` | Backend API URL | ❌ No | http://localhost:8000 |

## Performance Optimization

### Model Caching
The ASR model (~600MB) is downloaded on first run and cached in a Docker volume. This prevents re-downloading on container restarts.

```bash
# View cached models
docker volume inspect jobsathi_model_cache

# Remove cache to free space (model will re-download)
docker volume rm jobsathi_model_cache
```

### Resource Limits
Add resource limits in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          memory: 2G
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Host:Container
```

### Model Download Fails
```bash
# Check logs
docker-compose logs backend

# Verify internet connection
docker-compose exec backend curl -I https://huggingface.co

# Manually download model
docker-compose exec backend python -c "from transformers import AutoModel; AutoModel.from_pretrained('ai4bharat/indic-conformer-600m-multilingual')"
```

### Container Crashes
```bash
# View full logs
docker-compose logs --tail=200 backend

# Check container status
docker-compose ps

# Restart with fresh build
docker-compose down -v
docker-compose up --build
```

### Permission Denied (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker-compose up
```

## Production Deployment

For production, use additional configurations:

1. **Use production Dockerfile** with multi-stage builds
2. **Enable HTTPS** with reverse proxy (nginx/traefik)
3. **Set resource limits** and restart policies
4. **Use secrets management** instead of .env files
5. **Enable logging drivers** for centralized logging
6. **Use health checks** for automatic recovery
7. **Implement backup strategy** for database volume

Example production compose override:

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  backend:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

For issues or questions, please check the main README.md or open a GitHub issue.
