# Docker Deployment Guide
## CI/CD Health Dashboard

### Overview
This document provides comprehensive instructions for containerizing and deploying the CI/CD Health Dashboard using Docker and Docker Compose.

---

## 1. Containerization Strategy

### 1.1 Multi-Container Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Jenkins      │
│   Container     │    │   Container     │    │   Container     │
│                 │    │                 │    │                 │
│  • Express.js   │◄──►│  • FastAPI      │◄──►│  • Jenkins LTS  │
│  • EJS Templates│    │  • SQLite DB    │    │  • Build Jobs   │
│  • Bootstrap    │    │  • Email Service│    │  • REST API     │
│  • Port 3000    │    │  • Port 8000    │    │  • Port 8080    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1.2 Container Benefits
- **Isolation**: Each service runs in its own environment
- **Scalability**: Easy horizontal scaling of components
- **Consistency**: Same environment across development, staging, and production
- **Dependency Management**: All dependencies bundled with containers
- **Easy Deployment**: Single command deployment with Docker Compose

---

## 2. Dockerfile Configurations

### 2.1 Backend Dockerfile
```dockerfile
# /backend/Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 2.2 Frontend Dockerfile
```dockerfile
# /frontend/Dockerfile
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production --no-audit --no-fund

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start command
CMD ["npm", "start"]
```

### 2.3 Jenkins Dockerfile (Optional Custom)
```dockerfile
# /jenkins/Dockerfile (if custom Jenkins image needed)
FROM jenkins/jenkins:lts-jdk17

# Switch to root to install plugins
USER root

# Install additional tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Switch back to jenkins user
USER jenkins

# Copy custom configuration
COPY jenkins.yaml /usr/share/jenkins/ref/jenkins.yaml
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

# Install plugins
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
```

---

## 3. Docker Compose Configuration

### 3.1 Complete docker-compose.yml
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cicd-backend
    ports:
      - "8000:8000"
    environment:
      # Application settings
      DEBUG: "true"
      SECRET_KEY: "dev-secret-key-change-in-production"
      CORS_ORIGINS: "http://localhost:3000,http://127.0.0.1:3000"
      
      # Jenkins integration
      JENKINS_URL: "http://jenkins:8080"
      JENKINS_USERNAME: "admin"
      JENKINS_API_TOKEN: "119945a0409c8335bfdb889b602739a995"
      PUBLIC_BASE_URL: "http://localhost:8080"
      
      # Email configuration
      SMTP_SERVER: "smtp.gmail.com"
      SMTP_PORT: "587"
      SMTP_USERNAME: "ni33wagh@gmail.com"
      SMTP_PASSWORD: "ztlegvdbfotzxetu"
      FROM_EMAIL: "ni33wagh@gmail.com"
      TO_EMAIL: "ni33wagh@gmail.com"
      SMTP_USE_TLS: "true"
      
      # Database
      DATABASE_URL: "sqlite:///./cicd_dashboard.db"
    volumes:
      - ./backend:/app
      - backend_data:/app/data
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      jenkins:
        condition: service_healthy
    networks:
      - cicd-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: cicd-frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_BASE: "http://localhost:8000"
      BACKEND_URL: "http://backend:8000"
      PUBLIC_BACKEND_URL: "http://localhost:8000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: ["npm", "start"]
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - cicd-network

  jenkins:
    image: jenkins/jenkins:lts-jdk17
    container_name: cicd-jenkins
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "50000:50000"
    environment:
      JENKINS_OPTS: "--httpPort=8080"
      JAVA_OPTS: "-Djenkins.install.runSetupWizard=false"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - ./jenkins/jobs:/var/jenkins_home/jobs
      - ./jenkins/plugins:/var/jenkins_home/plugins
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    networks:
      - cicd-network

  # Optional: Database service for production
  postgres:
    image: postgres:13-alpine
    container_name: cicd-postgres
    environment:
      POSTGRES_DB: cicd_dashboard
      POSTGRES_USER: dashboard_user
      POSTGRES_PASSWORD: dashboard_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - cicd-network
    profiles:
      - production

volumes:
  jenkins_home:
    driver: local
  backend_data:
    driver: local
  postgres_data:
    driver: local

networks:
  cicd-network:
    driver: bridge
```

### 3.2 Environment Configuration
```bash
# .env file for environment variables
# Jenkins Configuration
JENKINS_URL=http://jenkins:8080
JENKINS_USERNAME=admin
JENKINS_API_TOKEN=your-api-token-here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=your-email@gmail.com

# Application Configuration
DEBUG=true
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Database Configuration
DATABASE_URL=sqlite:///./cicd_dashboard.db
# For production with PostgreSQL:
# DATABASE_URL=postgresql://dashboard_user:dashboard_password@postgres:5432/cicd_dashboard
```

---

## 4. Deployment Commands

### 4.1 Development Deployment
```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### 4.2 Production Deployment
```bash
# Build for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Scale services
docker-compose up --scale backend=3 --scale frontend=2

# Update services
docker-compose pull
docker-compose up -d
```

### 4.3 Service Management
```bash
# Restart specific service
docker-compose restart backend

# View service status
docker-compose ps

# Execute commands in container
docker-compose exec backend bash
docker-compose exec frontend npm install

# View service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs jenkins
```

---

## 5. Health Checks and Monitoring

### 5.1 Health Check Endpoints
```python
# Backend health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "jenkins": "connected",
            "email": "configured"
        }
    }
```

```javascript
// Frontend health check
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});
```

### 5.2 Monitoring Script
```bash
#!/bin/bash
# monitor.sh - Health monitoring script

echo "🔍 CI/CD Dashboard Health Check"
echo "================================"

# Check backend
echo "Backend Status:"
curl -s http://localhost:8000/api/health | jq '.' || echo "❌ Backend not responding"

# Check frontend
echo -e "\nFrontend Status:"
curl -s http://localhost:3000/health | jq '.' || echo "❌ Frontend not responding"

# Check Jenkins
echo -e "\nJenkins Status:"
curl -s http://localhost:8080/login | grep -q "Jenkins" && echo "✅ Jenkins responding" || echo "❌ Jenkins not responding"

# Check containers
echo -e "\nContainer Status:"
docker-compose ps
```

---

## 6. Backup and Recovery

### 6.1 Data Backup
```bash
#!/bin/bash
# backup.sh - Backup script

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR"

# Backup Jenkins data
docker-compose exec jenkins tar -czf - /var/jenkins_home | cat > "$BACKUP_DIR/jenkins_home.tar.gz"

# Backup database
docker-compose exec backend sqlite3 /app/cicd_dashboard.db ".backup /app/backup.db"
docker cp cicd-backend:/app/backup.db "$BACKUP_DIR/database.db"

# Backup configuration
cp docker-compose.yml "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"

echo "✅ Backup completed: $BACKUP_DIR"
```

### 6.2 Data Recovery
```bash
#!/bin/bash
# restore.sh - Restore script

BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "🔄 Restoring from $BACKUP_DIR"

# Stop services
docker-compose down

# Restore Jenkins data
docker-compose up -d jenkins
sleep 30
docker-compose exec jenkins tar -xzf - < "$BACKUP_DIR/jenkins_home.tar.gz"

# Restore database
docker-compose up -d backend
sleep 10
docker cp "$BACKUP_DIR/database.db" cicd-backend:/app/cicd_dashboard.db

# Restart all services
docker-compose up -d

echo "✅ Restore completed"
```

---

## 7. Security Considerations

### 7.1 Container Security
```dockerfile
# Security best practices in Dockerfile
FROM python:3.9-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Use specific versions
FROM node:16-alpine@sha256:abc123...

# Remove package manager cache
RUN npm ci --only=production && npm cache clean --force
```

### 7.2 Network Security
```yaml
# docker-compose.yml network configuration
networks:
  cicd-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 7.3 Secrets Management
```bash
# Use Docker secrets for sensitive data
echo "your-secret-password" | docker secret create smtp_password -
echo "your-api-token" | docker secret create jenkins_token -
```

---

## 8. Troubleshooting

### 8.1 Common Issues
```bash
# Container won't start
docker-compose logs <service_name>

# Port conflicts
docker-compose down
sudo lsof -i :3000  # Check port usage
docker-compose up

# Permission issues
sudo chown -R $USER:$USER ./jenkins_home
docker-compose up

# Database connection issues
docker-compose exec backend python -c "import sqlite3; print('DB OK')"
```

### 8.2 Performance Optimization
```yaml
# Resource limits in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

---

*This deployment guide provides complete instructions for containerizing and deploying the CI/CD Health Dashboard in any environment.*
