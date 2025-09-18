#!/bin/bash
# CI/CD Health Dashboard - EC2 User Data Script
# Generated with AI assistance for automated deployment

set -e

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/user-data.log
}

log "Starting CI/CD Health Dashboard deployment..."

# Update system packages
log "Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install required packages
log "Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    unzip \
    jq \
    htop \
    vim

# Install Docker
log "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Install Docker Compose (standalone)
log "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Create application directory
log "Creating application directory..."
mkdir -p /opt/${project_name}
cd /opt/${project_name}

# Clone the application repository (if using Git)
# Uncomment and modify the following lines if your code is in a Git repository
# log "Cloning application repository..."
# git clone https://github.com/your-username/cicd-health-dashboard.git .
# cd cicd-health-dashboard

# For this deployment, we'll create the application structure
log "Setting up application structure..."

# Create docker-compose.yml for production
cat > docker-compose.yml << 'EOF'
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
      DEBUG: "false"
      SECRET_KEY: "prod-secret-key-change-in-production"
      CORS_ORIGINS: "*"
      
      # Jenkins integration
      JENKINS_URL: "http://jenkins:8080"
      JENKINS_USERNAME: "admin"
      JENKINS_API_TOKEN: "119945a0409c8335bfdb889b602739a995"
      PUBLIC_BASE_URL: "http://jenkins:8080"
      
      # Email configuration
      SMTP_SERVER: "smtp.gmail.com"
      SMTP_PORT: "587"
      SMTP_USERNAME: "ni33wagh@gmail.com"
      SMTP_PASSWORD: "${SMTP_PASSWORD}"
      FROM_EMAIL: "ni33wagh@gmail.com"
      TO_EMAIL: "ni33wagh@gmail.com"
      SMTP_USE_TLS: "true"
      
      # Database
      DATABASE_URL: "sqlite:///./cicd_dashboard.db"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
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
      - ./logs:/app/logs
    restart: unless-stopped
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

volumes:
  jenkins_home:
    driver: local

networks:
  cicd-network:
    driver: bridge
EOF

# Create necessary directories
log "Creating application directories..."
mkdir -p data logs jenkins/jobs jenkins/plugins

# Set proper permissions
chown -R ubuntu:ubuntu /opt/${project_name}
chmod -R 755 /opt/${project_name}

# Create environment file
log "Creating environment configuration..."
cat > .env << EOF
# Environment: ${environment}
# Project: ${project_name}

# Jenkins Configuration
JENKINS_URL=http://jenkins:8080
JENKINS_USERNAME=admin
JENKINS_API_TOKEN=119945a0409c8335bfdb889b602739a995

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=ni33wagh@gmail.com
SMTP_PASSWORD=
FROM_EMAIL=ni33wagh@gmail.com
TO_EMAIL=ni33wagh@gmail.com

# Application Configuration
DEBUG=false
SECRET_KEY=prod-secret-key-change-in-production
CORS_ORIGINS=*

# Database Configuration
DATABASE_URL=sqlite:///./cicd_dashboard.db
EOF

# Create systemd service for application
log "Creating systemd service..."
cat > /etc/systemd/system/cicd-dashboard.service << EOF
[Unit]
Description=CI/CD Health Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/${project_name}
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# Create health check script
log "Creating health check script..."
cat > /opt/${project_name}/health-check.sh << 'EOF'
#!/bin/bash
# Health check script for CI/CD Dashboard

check_service() {
    local service_name=$1
    local port=$2
    local path=${3:-/}
    
    if curl -s -f "http://localhost:${port}${path}" > /dev/null; then
        echo "✅ ${service_name} is healthy"
        return 0
    else
        echo "❌ ${service_name} is not responding"
        return 1
    fi
}

echo "🔍 CI/CD Dashboard Health Check - $(date)"
echo "=========================================="

# Check services
check_service "Backend API" 8000 "/api/health"
check_service "Frontend" 3000 "/health"
check_service "Jenkins" 8080 "/login"

# Check Docker containers
echo ""
echo "📦 Docker Container Status:"
docker-compose ps

# Check system resources
echo ""
echo "💻 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"
EOF

chmod +x /opt/${project_name}/health-check.sh

# Create backup script
log "Creating backup script..."
cat > /opt/${project_name}/backup.sh << 'EOF'
#!/bin/bash
# Backup script for CI/CD Dashboard

BACKUP_DIR="/opt/${project_name}/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR"

# Backup application data
cp -r /opt/${project_name}/data "$BACKUP_DIR/"
cp /opt/${project_name}/.env "$BACKUP_DIR/"

# Backup Jenkins data
docker-compose exec -T jenkins tar -czf - /var/jenkins_home | cat > "$BACKUP_DIR/jenkins_home.tar.gz"

echo "✅ Backup completed: $BACKUP_DIR"
EOF

chmod +x /opt/${project_name}/backup.sh

# Create log rotation configuration
log "Setting up log rotation..."
cat > /etc/logrotate.d/cicd-dashboard << EOF
/opt/${project_name}/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        docker-compose restart backend frontend
    endscript
}
EOF

# Install CloudWatch agent (optional)
log "Installing CloudWatch agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E amazon-cloudwatch-agent.deb

# Create CloudWatch configuration
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/${project_name}/logs/*.log",
                        "log_group_name": "/aws/ec2/${project_name}",
                        "log_stream_name": "{instance_id}/application.log"
                    },
                    {
                        "file_path": "/var/log/user-data.log",
                        "log_group_name": "/aws/ec2/${project_name}",
                        "log_stream_name": "{instance_id}/user-data.log"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "CWAgent",
        "metrics_collected": {
            "cpu": {
                "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": ["used_percent"],
                "metrics_collection_interval": 60,
                "resources": ["*"]
            },
            "mem": {
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
    -s

# Enable and start the application service
log "Enabling and starting application service..."
systemctl daemon-reload
systemctl enable cicd-dashboard.service

# Wait for Docker to be ready
log "Waiting for Docker to be ready..."
sleep 30

# Start the application
log "Starting CI/CD Health Dashboard..."
systemctl start cicd-dashboard.service

# Wait for services to start
log "Waiting for services to start..."
sleep 60

# Run initial health check
log "Running initial health check..."
/opt/${project_name}/health-check.sh

# Create a simple status page
log "Creating status page..."
cat > /opt/${project_name}/status.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>CI/CD Dashboard Status</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .healthy { background-color: #d4edda; color: #155724; }
        .unhealthy { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>CI/CD Health Dashboard Status</h1>
    <p>Last updated: <span id="timestamp"></span></p>
    
    <div class="status healthy">
        <h3>✅ Deployment Complete</h3>
        <p>CI/CD Health Dashboard has been successfully deployed!</p>
    </div>
    
    <h2>Access URLs:</h2>
    <ul>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000">Dashboard Frontend</a></li>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000">Backend API</a></li>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs">API Documentation</a></li>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080">Jenkins</a></li>
    </ul>
    
    <script>
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
EOF

# Serve status page with Python (simple HTTP server)
nohup python3 -m http.server 8080 --directory /opt/${project_name} > /dev/null 2>&1 &

log "CI/CD Health Dashboard deployment completed successfully!"
log "Dashboard URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
log "Jenkins URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
log "API URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"

# Signal completion
touch /opt/${project_name}/deployment-complete.flag
