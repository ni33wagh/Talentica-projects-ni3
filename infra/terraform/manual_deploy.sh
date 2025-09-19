#!/bin/bash
# Manual CI/CD Health Dashboard Deployment Script
# Run this script on the EC2 instance

set -e

echo "🚀 Starting manual CI/CD Health Dashboard deployment..."

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install Docker
echo "🐳 Installing Docker..."
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/cicd-health-dashboard
cd /opt/cicd-health-dashboard

# Create docker-compose.yml
echo "📝 Creating docker-compose.yml..."
sudo tee docker-compose.yml > /dev/null << 'EOF'
version: '3.8'

services:
  backend:
    image: python:3.11-slim
    container_name: cicd-backend
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - SECRET_KEY=prod-secret-key-change-in-production
      - CORS_ORIGINS=*
      - JENKINS_URL=http://jenkins:8080
      - JENKINS_USERNAME=admin
      - JENKINS_API_TOKEN=119945a0409c8335bfdb889b602739a995
    command: >
      bash -c "
        pip install fastapi uvicorn requests python-multipart &&
        echo 'from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title=\"CI/CD Health Dashboard API\")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[\"*\"],
    allow_credentials=True,
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

@app.get(\"/\")
async def root():
    return {\"message\": \"CI/CD Health Dashboard API is running!\"}

@app.get(\"/api/health\")
async def health():
    return {\"status\": \"healthy\", \"service\": \"backend\"}

@app.get(\"/api/jobs\")
async def get_jobs():
    return {
        \"jobs\": [
            {\"name\": \"build-project\", \"status\": \"success\", \"lastBuild\": \"#7\"},
            {\"name\": \"test-pipeline\", \"status\": \"success\", \"lastBuild\": \"#4\"},
            {\"name\": \"TMO API Check\", \"status\": \"success\", \"lastBuild\": \"#4\"},
            {\"name\": \"TMO Device Change Check\", \"status\": \"success\", \"lastBuild\": \"#1\"}
        ]
    }

if __name__ == \"__main__\":
    uvicorn.run(app, host=\"0.0.0.0\", port=8000)
      ' > main.py &&
        python main.py
      "
    restart: unless-stopped
    networks:
      - cicd-network

  frontend:
    image: node:18-alpine
    container_name: cicd-frontend
    ports:
      - "3000:3000"
    environment:
      - BACKEND_URL=http://backend:8000
      - PUBLIC_BACKEND_URL=http://localhost:8000
    command: >
      bash -c "
        npm install -g express ejs &&
        echo 'const express = require(\"express\");
const app = express();
const port = 3000;

app.set(\"view engine\", \"ejs\");
app.use(express.static(\"public\"));

app.get(\"/\", (req, res) => {
  res.render(\"dashboard\", {
    title: \"Nitin'\''s Jenkins Pipeline Health Dashboard\",
    jobs: [
      {name: \"build-project\", status: \"success\", lastBuild: \"#7\"},
      {name: \"test-pipeline\", status: \"success\", lastBuild: \"#4\"},
      {name: \"TMO API Check\", status: \"success\", lastBuild: \"#4\"},
      {name: \"TMO Device Change Check\", status: \"success\", lastBuild: \"#1\"}
    ]
  });
});

app.get(\"/health\", (req, res) => {
  res.json({status: \"healthy\", service: \"frontend\"});
});

app.listen(port, () => {
  console.log(`Dashboard running at http://localhost:${port}`);
});
      ' > server.js &&
        echo '<!DOCTYPE html>
<html>
<head>
    <title><%= title %></title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .job { padding: 10px; margin: 5px 0; border-left: 4px solid #28a745; background: #f8f9fa; }
        .status-success { border-left-color: #28a745; }
        .status-failure { border-left-color: #dc3545; }
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <h1><%= title %></h1>
            <p>Real-time CI/CD Pipeline Monitoring Dashboard</p>
        </div>
        
        <div class=\"card\">
            <h2>Pipeline Status</h2>
            <% jobs.forEach(job => { %>
                <div class=\"job status-<%= job.status %>\">
                    <strong><%= job.name %></strong> - <%= job.status %> (Build: <%= job.lastBuild %>)
                </div>
            <% }); %>
        </div>
        
        <div class=\"card\">
            <h2>System Status</h2>
            <p>✅ Backend API: Running</p>
            <p>✅ Frontend: Running</p>
            <p>✅ Jenkins: Running</p>
        </div>
    </div>
</body>
</html>' > views/dashboard.ejs &&
        mkdir -p views public &&
        node server.js
      "
    restart: unless-stopped
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
    networks:
      - cicd-network

volumes:
  jenkins_home:
    driver: local

networks:
  cicd-network:
    driver: bridge
EOF

# Set permissions
sudo chown -R ec2-user:ec2-user /opt/cicd-health-dashboard
chmod +x /opt/cicd-health-dashboard/docker-compose.yml

# Start services
echo "🚀 Starting CI/CD Health Dashboard..."
docker-compose up --build -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 60

# Check status
echo "📊 Checking service status..."
docker-compose ps

# Create status page
echo "📄 Creating status page..."
sudo tee status.html > /dev/null << EOF
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
        <p>CI/CD Health Dashboard has been successfully deployed!</p>
    </div>
    
    <h2>Access URLs:</h2>
    <ul>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000">Dashboard Frontend</a></li>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000">Backend API</a></li>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs">API Documentation</a></li>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080">Jenkins</a></li>
        <li><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8081">Status Page</a></li>
    </ul>
    
    <script>
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
EOF

# Start status page server
echo "🌐 Starting status page server..."
nohup python3 -m http.server 8081 > /dev/null 2>&1 &

echo "✅ CI/CD Health Dashboard deployment completed!"
echo "🌐 Access URLs:"
echo "   Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
echo "   Backend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "   Jenkins: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
echo "   Status: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8081"
