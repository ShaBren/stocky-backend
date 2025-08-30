# Stocky Backend Deployment Guide

## Overview

This guide covers deploying the Stocky Backend v0.0.1 using Docker. The application is containerized and ready for production deployment.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 512MB+ available memory
- 1GB+ available disk space

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd stocky-backend
```

### 2. Deploy with Docker Compose

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000`

### 3. Verify Deployment

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status":"healthy","service":"stocky-backend"}
```

## Configuration

### Environment Variables

The following environment variables can be configured in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+pysqlite:///./data/stocky.db` | Database connection string |
| `SECRET_KEY` | `your-secret-key-change-in-production-v001` | JWT signing key (CHANGE IN PRODUCTION) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |
| `CORS_ORIGINS` | `["http://localhost:3000","http://127.0.0.1:3000"]` | Allowed CORS origins |
| `CREATE_INITIAL_DATA` | `true` | Create initial database data |

### Production Configuration

For production deployment, ensure you:

1. **Change the SECRET_KEY**:
   ```yaml
   environment:
     - SECRET_KEY=your-super-secure-secret-key-here
   ```

2. **Configure CORS origins** for your frontend:
   ```yaml
   environment:
     - CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
   ```

3. **Use external database** (optional):
   ```yaml
   environment:
     - DATABASE_URL=postgresql://user:password@host:port/database
   ```

## Docker Configuration

### Build Options

Build the image manually:
```bash
docker build -t stocky-backend:v0.0.1 .
```

### Volume Management

Data is persisted in the `stocky_data` Docker volume:

```bash
# Backup data
docker run --rm -v stocky_data:/data -v $(pwd):/backup alpine tar czf /backup/stocky-backup.tar.gz -C /data .

# Restore data
docker run --rm -v stocky_data:/data -v $(pwd):/backup alpine tar xzf /backup/stocky-backup.tar.gz -C /data
```

### Resource Limits

For production, consider adding resource limits:

```yaml
services:
  backend:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

## Production Deployment

### Docker Swarm

1. Initialize swarm (if not already done):
   ```bash
   docker swarm init
   ```

2. Deploy stack:
   ```bash
   docker stack deploy -c docker-compose.yml stocky
   ```

### Kubernetes

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stocky-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stocky-backend
  template:
    metadata:
      labels:
        app: stocky-backend
    spec:
      containers:
      - name: stocky-backend
        image: stocky-backend:v0.0.1
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: stocky-secrets
              key: secret-key
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: stocky-data
---
apiVersion: v1
kind: Service
metadata:
  name: stocky-backend-service
spec:
  selector:
    app: stocky-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Checks

The application provides a health endpoint:
- **URL**: `/api/v1/health`
- **Method**: GET
- **Response**: `{"status":"healthy","service":"stocky-backend"}`

### Docker Health Check

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    # ... other config
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Logs

View application logs:
```bash
docker-compose logs -f backend
```

## Security

### SSL/TLS

For production, always use HTTPS:

1. **With reverse proxy**: Configure SSL at the proxy level
2. **Direct deployment**: Use a service like Cloudflare or AWS ALB

### Firewall

Ensure only necessary ports are exposed:
- Port 8000: Only to reverse proxy or load balancer
- Database ports: Only to application containers

### Secrets Management

Never commit secrets to version control:

1. Use environment variables
2. Use Docker secrets (Swarm) or Kubernetes secrets
3. Use external secret management (AWS Secrets Manager, HashiCorp Vault)

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Check database URL format
   - Verify volume permissions
   - Check database file exists

2. **Port already in use**:
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

3. **Out of memory**:
   - Increase Docker memory limits
   - Check application memory usage

### Debug Mode

Enable debug logging:
```yaml
environment:
  - DEBUG=true
```

### Container Access

Access running container:
```bash
docker-compose exec backend bash
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec backend sqlite3 /app/data/stocky.db ".backup /app/data/backup.db"

# Copy backup from container
docker cp $(docker-compose ps -q backend):/app/data/backup.db ./backup.db
```

### Full Backup

```bash
# Backup entire data volume
docker run --rm -v stocky_data:/data -v $(pwd):/backup alpine tar czf /backup/stocky-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

## Scaling

### Horizontal Scaling

For horizontal scaling, consider:

1. **External database**: Move from SQLite to PostgreSQL/MySQL
2. **Session storage**: Use Redis for session management
3. **Load balancer**: Distribute traffic across instances

### Vertical Scaling

Increase container resources:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
```

## Performance Tuning

### Database Optimization

1. **Connection pooling**: Configure SQLAlchemy pool settings
2. **Indexes**: Add database indexes for frequently queried fields
3. **Query optimization**: Use SQLAlchemy query optimization

### Application Optimization

1. **Workers**: Increase Uvicorn workers for CPU-bound tasks
2. **Caching**: Implement Redis caching for frequent queries
3. **Async operations**: Use async/await for I/O operations

## Support

For issues and support:
- Check application logs: `docker-compose logs backend`
- Review this deployment guide
- Check the main README.md for development setup
- Verify environment configuration

## Version Information

- **Application Version**: v0.0.1
- **Docker Image**: Built with Python 3.13-slim
- **Database**: SQLite (production: PostgreSQL recommended)
- **Web Server**: Uvicorn ASGI server
