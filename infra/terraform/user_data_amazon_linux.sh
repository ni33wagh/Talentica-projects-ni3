#!/bin/bash
# CI/CD Health Dashboard - Amazon Linux EC2 User Data Script
# Generated with AI assistance for automated deployment

set -e

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/user-data.log
}

log "Starting CI/CD Health Dashboard deployment on Amazon Linux..."

# Update system packages
log "Updating system packages..."
yum update -y

# Install required packages
log "Installing required packages..."
yum install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    vim \
    jq \
    python3 \
    python3-pip

# Install Docker
log "Installing Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
log "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Create application directory
log "Creating application directory..."
mkdir -p /opt/cicd-health-dashboard
cd /opt/cicd-health-dashboard

# Clone the repository
log "Cloning CI/CD Health Dashboard repository..."
git clone https://github.com/ni33wagh/cicd-health-dashboard.git .

# Wait for Docker to be ready
log "Waiting for Docker to be ready..."
sleep 30

# Start the application using existing docker-compose.yml
log "Starting CI/CD Health Dashboard with Docker Compose..."
docker-compose up --build -d

# Wait for services to start
log "Waiting for services to start..."
sleep 120

# Set proper permissions
chown -R ec2-user:ec2-user /opt/cicd-health-dashboard
chmod -R 755 /opt/cicd-health-dashboard

# Run health check
log "Running health check..."
docker-compose ps

# Create simple status page
log "Creating status page..."
cat > /opt/cicd-health-dashboard/status.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>CI/CD Dashboard Status</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .healthy { background-color: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <h1>CI/CD Health Dashboard Status</h1>
    <p>Last updated: <span id="timestamp"></span></p>
    
    <div class="status healthy">
        <h3>✅ Deployment Complete</h3>
        <p>CI/CD Health Dashboard has been successfully deployed on Amazon Linux!</p>
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

log "CI/CD Health Dashboard deployment completed successfully on Amazon Linux!"
log "Dashboard URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
log "Jenkins URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
log "API URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"

# Signal completion
touch /opt/cicd-health-dashboard/deployment-complete.flag
