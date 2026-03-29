# Docker Setup Guide

This document provides instructions for building and running the educational-equity-flow dashboard using Docker and Docker Compose.

## Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- 2GB+ free disk space
- 2GB+ available RAM

## Quick Start

### Option 1: Docker Compose (Recommended for Local Development)

```bash
# Start all services (dashboard + artifacts server)
docker-compose up -d

# View logs
docker-compose logs -f dashboard

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

The dashboard will be available at:
- **Dashboard**: http://localhost:8501
- **Artifacts Server**: http://localhost:8080/artifacts

### Option 2: Build and Run Manually

```bash
# Build image locally
docker build -t educational-equity-flow:latest .

# Run container
docker run -it --rm \
  -p 8501:8501 \
  -v $(pwd)/warehouse:/app/warehouse \
  -v $(pwd)/data:/app/data \
  educational-equity-flow:latest

# Access dashboard
# Open http://localhost:8501 in your browser
```

## Image Details

### Multi-Stage Build

The `Dockerfile` uses a **multi-stage build** approach:

1. **Builder Stage**: Installs build dependencies and Python packages
2. **Runtime Stage**: Minimal final image with only runtime dependencies

**Benefits**:
- Smaller final image (1.35GB vs 2.5GB+)
- Faster startup times
- Reduced security surface

### Image Specifications

| Component | Version |
|-----------|---------|
| Base Image | `python:3.11-slim` |
| Python | 3.11.x |
| Streamlit | 1.39.0 |
| Key Libraries | scikit-learn, Prophet, dbt, DuckDB |
| Final Size | ~1.35GB |
| User | `appuser` (non-root) |

### Health Check

The container includes a built-in health check:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start period**: 40 seconds (allows app initialization)
- **Retries**: 3 attempts before marking unhealthy

View health status:
```bash
docker-compose ps
# or
docker inspect educational-equity-flow-dashboard
```

## Docker Compose Services

### Service: Dashboard
- **Image**: `educational-equity-flow:latest`
- **Port**: `8501:8501`
- **Volumes**:
  - `/warehouse` - Persistent database and artifacts
  - `/data` - Raw data files
- **Restart**: Unless stopped
- **Health Check**: Enabled

### Service: Artifacts
- **Image**: `nginx:1.25-alpine`
- **Port**: `8080:80`
- **Purpose**: Serve warehouse artifacts as static files
- **Readiness**: Depends on dashboard

## Common Tasks

### Rebuild Image
```bash
# Full rebuild without cache
docker-compose build --no-cache

# Or manually
docker build --no-cache -t educational-equity-flow:latest .
```

### View Real-Time Logs
```bash
# Dashboard logs
docker-compose logs -f dashboard

# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Access Container Shell
```bash
docker-compose exec dashboard /bin/bash

# Or directly
docker run -it --rm educational-equity-flow:latest /bin/bash
```

### Run One-Off Commands
```bash
# Execute Python script
docker run --rm educational-equity-flow:latest \
  python -c "import streamlit; print('OK')"

# Run tests (if installed)
docker run --rm educational-equity-flow:latest \
  pytest tests/
```

### Persist Database Between Runs
The `warehouse` volume automatically persists across container restarts:
```bash
docker-compose down  # Stops containers but keeps volumes
docker-compose up    # Restarts with preserved data
```

To clear persisted data:
```bash
docker-compose down -v  # -v removes volumes
```

## Environment Variables

Set environment variables in `docker-compose.yml` or with `.env` file:

```yaml
# docker-compose.yml
environment:
  - STREAMLIT_CONFIG_LOGGER_LEVEL=info
  - STREAMLIT_CLIENT_SHOWERRORDETAILS=true
```

Or create `.env`:
```bash
STREAMLIT_CONFIG_LOGGER_LEVEL=info
STREAMLIT_CLIENT_SHOWERRORDETAILS=true
```

## Performance Optimization

### Reduce Image Size
Current: 1.35GB

**For production**, optimize further:
1. Use `python:3.11-alpine` (300MB, but loses some packages)
2. Remove development dependencies from runtime stage
3. Strip unnecessary packages after installation

### Speed Up Builds
```bash
# Use BuildKit (faster build engine)
export DOCKER_BUILDKIT=1
docker build .

# Use Docker Compose build cache
docker-compose build --no-cache
```

### Memory Usage

Default memory limits in `docker-compose.yml`:
- None set (uses host resources)

To limit:
```yaml
services:
  dashboard:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs dashboard

# Verify image exists
docker images | grep educational-equity-flow

# Rebuild image
docker-compose build --no-cache
```

### Port Already in Use
```bash
# Change port in docker-compose.yml
ports:
  - "8502:8501"  # Use 8502 instead

# Or find and stop conflicting container
lsof -i :8501
docker stop <container_id>
```

### Dashboard API Errors
```bash
# Verify database connectivity
docker-compose exec dashboard python -c "import duckdb; print('OK')"

# Check warehouse directory permissions
docker-compose exec dashboard ls -la /app/warehouse
```

### Memory Issues
```bash
# Increase Docker Desktop memory limit in settings
# Or use memory limits in compose file

# Check current memory usage
docker stats
```

## Security Best Practices

✅ **Implemented in Dockerfile**:
- Non-root user (`appuser`)
- Official Python base image
- Minimal attack surface

✅ **Additional recommendations**:
- Use private registry for production
- Scan image for vulnerabilities: `docker scan educational-equity-flow:latest`
- Enable image signing for CI/CD
- Use read-only root filesystem (if applicable)

## Production Deployment

### Docker Hub / GitHub Container Registry

Images are automatically built and pushed on:
- Commits to `master` branch
- Weekly schedule (security updates)
- Manual trigger via Actions

**Requirements**:
- DockerHub: Set `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
- GHCR: Automatic with `GITHUB_TOKEN`

### Kubernetes Deployment

Example deployment manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: educational-equity-flow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dashboard
  template:
    metadata:
      labels:
        app: dashboard
    spec:
      containers:
      - name: dashboard
        image: ghcr.io/theo-lyd/educational-equity-flow:latest
        ports:
        - containerPort: 8501
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import streamlit; print('healthy')"
          initialDelaySeconds: 40
          periodSeconds: 30
```

## Maintenance

### Update Dependencies
```bash
# Rebuild image to get latest package versions
docker-compose build --no-cache dashboard

# Or trigger via GitHub Actions
# Push to master with changes to pyproject.toml
```

### Clear Old Images
```bash
# Remove unused images
docker image prune

# Remove including dangling
docker image prune -a

# Check image sizes
docker images
```

### Monitor Container Health
```bash
# Check health status
docker-compose ps

# View detailed health info
docker inspect educational-equity-flow-dashboard | grep -A 5 Health

# Manually test
docker-compose exec dashboard python -c "import streamlit; print('OK')"
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Streamlit Docker Deployment](https://docs.streamlit.io/deploy/tutorials/docker)
- [Best Practices for Python Docker Images](https://docs.docker.com/language/python/build-images/)
