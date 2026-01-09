# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

## Local Development

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ground-ops-platform
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your API keys and configuration:

```env
# Required API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
FLIGHTAWARE_API_KEY=your_key_here

# Database (default for local)
DATABASE_URL=postgresql://groundops:groundops@localhost:5432/groundops

# Optional
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 4. Initialize Database

```bash
# Run migrations (if using Alembic)
docker-compose exec backend alembic upgrade head

# Or create tables directly
docker-compose exec backend python -c "from models.database import Base, engine; import asyncio; asyncio.run(Base.metadata.create_all(engine))"
```

### 5. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
open http://localhost:3000
```

## Production Deployment

### Option 1: Docker on Cloud VM

#### 1. Provision Infrastructure

```bash
# Example: AWS EC2
- Instance type: t3.large or larger
- OS: Ubuntu 22.04
- Storage: 100GB SSD
- Security groups:
  - 22 (SSH)
  - 80 (HTTP)
  - 443 (HTTPS)
  - 8000 (API - behind load balancer only)
```

#### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 3. Deploy Application

```bash
# Clone repository
git clone <repository-url>
cd ground-ops-platform

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Set production settings
export ENVIRONMENT=production
export DEBUG=false

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 4. Setup SSL with Nginx

```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/groundops

# Nginx configuration (see below)

# Enable site
sudo ln -s /etc/nginx/sites-available/groundops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

**Nginx Configuration:**
```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

### Option 2: Kubernetes

#### 1. Build Images

```bash
# Backend
docker build -t groundops-backend:latest ./backend

# Frontend
docker build -t groundops-frontend:latest ./frontend

# Push to registry
docker tag groundops-backend:latest your-registry/groundops-backend:latest
docker push your-registry/groundops-backend:latest
```

#### 2. Apply Kubernetes Manifests

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

### Option 3: Cloud-Native (AWS)

#### Services Architecture

- **ECS Fargate**: Backend and Celery workers
- **RDS PostgreSQL**: Database
- **ElastiCache Redis**: Cache and broker
- **S3**: Static assets and ML models
- **CloudFront**: CDN for frontend
- **ALB**: Load balancer
- **CloudWatch**: Monitoring and logs

## Database Migrations

### Using Alembic

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migration
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## Monitoring

### Application Logs

```bash
# View backend logs
docker-compose logs -f backend

# View Celery logs
docker-compose logs -f celery-worker

# View frontend logs
docker-compose logs -f frontend
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database connectivity
docker-compose exec backend python -c "from models.database import engine; print('DB OK')"

# Redis connectivity
docker-compose exec redis redis-cli ping
```

## Backup and Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U groundops groundops > backup.sql

# Restore
docker-compose exec -T postgres psql -U groundops groundops < backup.sql
```

### ML Models Backup

```bash
# Backup models directory
tar -czf models-backup.tar.gz ml/models/

# Upload to S3
aws s3 cp models-backup.tar.gz s3://your-bucket/backups/
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale Celery workers
docker-compose up -d --scale celery-worker=5
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Security Checklist

- [ ] Change default passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall rules
- [ ] Set up API rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Secrets management (AWS Secrets Manager, HashiCorp Vault)
- [ ] Database encryption at rest
- [ ] Network encryption in transit
- [ ] CORS configuration
- [ ] Input validation
- [ ] SQL injection prevention

## Performance Optimization

1. **Database**
   - Add indexes on frequently queried columns
   - Use connection pooling
   - Enable query caching
   - Partition large tables

2. **API**
   - Enable response caching
   - Use async operations
   - Optimize database queries
   - Implement pagination

3. **Frontend**
   - Code splitting
   - Lazy loading
   - CDN for static assets
   - Image optimization

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database not ready: Wait for postgres health check
# - Missing environment variables: Check .env file
# - Port conflict: Change port in docker-compose.yml
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec backend python -c "from models.database import engine; engine.connect()"

# Check credentials
docker-compose exec postgres psql -U groundops -d groundops -c "SELECT 1"
```

### Celery Tasks Not Running

```bash
# Check worker status
docker-compose logs celery-worker

# Inspect queue
docker-compose exec redis redis-cli LLEN celery

# Restart workers
docker-compose restart celery-worker celery-beat
```

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres vacuumdb -U groundops groundops

# Analyze tables
docker-compose exec postgres psql -U groundops -d groundops -c "ANALYZE"
```
