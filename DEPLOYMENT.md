# Deployment Guide

This guide covers deploying the AI Coaching Platform to AWS, GCP, and other cloud providers.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [AWS Deployment](#aws-deployment)
- [GCP Deployment](#gcp-deployment)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Monitoring and Logs](#monitoring-and-logs)

## Prerequisites

- Docker and Docker Compose installed
- Cloud provider account (AWS/GCP)
- Domain name (optional, for production)
- API keys for OpenAI, Anthropic, and DeepSeek

## Local Development

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ChineseAICoaching
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
SECRET_KEY=your_secret_key_here
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Seed Initial Lessons

```bash
docker-compose exec backend python seed_lessons.py
```

### 5. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## AWS Deployment

### Option 1: AWS ECS (Elastic Container Service)

#### 1. Prerequisites

- AWS CLI configured
- ECR repositories created
- ECS cluster created

#### 2. Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag images
docker build -t aicoaching-backend:latest ./backend
docker build -t aicoaching-frontend:latest ./frontend

docker tag aicoaching-backend:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/aicoaching-backend:latest
docker tag aicoaching-frontend:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/aicoaching-frontend:latest

# Push to ECR
docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/aicoaching-backend:latest
docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/aicoaching-frontend:latest
```

#### 3. Set Up RDS (PostgreSQL)

```bash
aws rds create-db-instance \
  --db-instance-identifier aicoaching-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username aicoach \
  --master-user-password <your-password> \
  --allocated-storage 20
```

#### 4. Set Up ElastiCache (Redis)

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id aicoaching-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

#### 5. Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "aicoaching",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/aicoaching-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://aicoach:<password>@<rds-endpoint>:5432/aicoaching"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/aicoaching",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
```

#### 6. Create ECS Service

```bash
aws ecs create-service \
  --cluster aicoaching-cluster \
  --service-name aicoaching-service \
  --task-definition aicoaching \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Option 2: AWS EC2 with Docker Compose

#### 1. Launch EC2 Instance

```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups aicoaching-sg \
  --user-data file://user-data.sh
```

#### 2. SSH into Instance and Deploy

```bash
ssh -i your-key.pem ec2-user@<instance-ip>

# Clone repository
git clone <repository-url>
cd ChineseAICoaching

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up -d

# Seed lessons
docker-compose exec backend python seed_lessons.py
```

## GCP Deployment

### Option 1: Google Cloud Run

#### 1. Build and Push to Container Registry

```bash
# Configure gcloud
gcloud auth configure-docker

# Build images
docker build -t gcr.io/<project-id>/aicoaching-backend:latest ./backend
docker build -t gcr.io/<project-id>/aicoaching-frontend:latest ./frontend

# Push to GCR
docker push gcr.io/<project-id>/aicoaching-backend:latest
docker push gcr.io/<project-id>/aicoaching-frontend:latest
```

#### 2. Set Up Cloud SQL (PostgreSQL)

```bash
gcloud sql instances create aicoaching-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create aicoaching --instance=aicoaching-db

gcloud sql users create aicoach \
  --instance=aicoaching-db \
  --password=<your-password>
```

#### 3. Deploy to Cloud Run

```bash
# Backend
gcloud run deploy aicoaching-backend \
  --image gcr.io/<project-id>/aicoaching-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://...,OPENAI_API_KEY=...,ANTHROPIC_API_KEY=...

# Frontend
gcloud run deploy aicoaching-frontend \
  --image gcr.io/<project-id>/aicoaching-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=https://<backend-url>
```

### Option 2: GCP Compute Engine with Docker Compose

#### 1. Create VM Instance

```bash
gcloud compute instances create aicoaching-vm \
  --machine-type=e2-medium \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --tags=http-server,https-server
```

#### 2. SSH and Deploy

```bash
gcloud compute ssh aicoaching-vm --zone=us-central1-a

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone <repository-url>
cd ChineseAICoaching
cp .env.example .env
# Edit .env

sudo docker-compose up -d
```

## Environment Variables

### Required Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://host:port/0

# AI APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...

# Application
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=production

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

### Optional Variables

```env
ACCESS_TOKEN_EXPIRE_MINUTES=30
ANALYSIS_INTERVAL_DAYS=7
MIN_SESSIONS_FOR_ANALYSIS=3
```

## Database Migrations

### Using Alembic (Recommended for Production)

```bash
# Install Alembic in backend
docker-compose exec backend pip install alembic

# Initialize Alembic
docker-compose exec backend alembic init alembic

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Initial migration"

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Manual Schema Creation

The application automatically creates tables on startup in development mode. For production:

```bash
docker-compose exec backend python -c "
from app.database import sync_engine, Base
from app.models import *
Base.metadata.create_all(bind=sync_engine)
"
```

## Monitoring and Logs

### Docker Compose Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### AWS CloudWatch

Configure in ECS task definition:

```json
"logConfiguration": {
  "logDriver": "awslogs",
  "options": {
    "awslogs-group": "/ecs/aicoaching",
    "awslogs-region": "us-east-1",
    "awslogs-stream-prefix": "backend"
  }
}
```

### GCP Cloud Logging

Automatically enabled for Cloud Run. View logs:

```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

## Health Checks

### Backend Health Endpoint

```bash
curl http://localhost:8001/health
```

### Database Connection

```bash
docker-compose exec backend python -c "
from app.database import async_engine
import asyncio
async def test():
    async with async_engine.connect() as conn:
        print('Database connected successfully')
asyncio.run(test())
"
```

## Scaling

### Horizontal Scaling

#### AWS ECS

```bash
aws ecs update-service \
  --cluster aicoaching-cluster \
  --service aicoaching-service \
  --desired-count 4
```

#### GCP Cloud Run

```bash
gcloud run services update aicoaching-backend \
  --min-instances 2 \
  --max-instances 10
```

### Vertical Scaling

Update instance types/sizes in your cloud provider console or infrastructure as code.

## Security Best Practices

1. **Use Secrets Management**
   - AWS: Secrets Manager or Parameter Store
   - GCP: Secret Manager
   - Never commit secrets to version control

2. **Enable HTTPS**
   - Use AWS Certificate Manager or Let's Encrypt
   - Configure SSL/TLS in nginx or load balancer

3. **Network Security**
   - Use VPC/Private subnets for databases
   - Configure security groups/firewall rules
   - Enable DDoS protection

4. **Regular Updates**
   - Keep Docker images updated
   - Apply security patches
   - Monitor CVE databases

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify network connectivity
   - Check security group/firewall rules

2. **API Keys Invalid**
   - Verify API keys are correct
   - Check rate limits
   - Ensure proper environment variable names

3. **Container Won't Start**
   - Check logs: `docker-compose logs <service>`
   - Verify environment variables
   - Check health check configuration

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: See README.md
