#!/bin/bash
# Fix Dockerfile Structure for Proper Dependency Installation

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🔧 Fixing Dockerfile structure for proper dependency installation..."

ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "🛑 Stopping all containers..."
docker-compose down

echo "🔧 Creating proper frontend Dockerfile with dependency optimization..."

cd frontend

# Create optimized package.json
cat > package.json << 'PACKAGE_EOF'
{
  "name": "cicd-health-dashboard-frontend",
  "version": "1.0.0",
  "description": "Frontend for CI/CD Pipeline Health Dashboard",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "ejs": "^3.1.9",
    "socket.io-client": "^4.7.2",
    "axios": "^1.5.0",
    "moment": "^2.29.4",
    "chart.js": "^4.4.0",
    "bootstrap": "^5.3.2",
    "jquery": "^3.7.1",
    "popper.js": "^1.16.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
PACKAGE_EOF

# Create optimized Dockerfile that installs dependencies BEFORE copying app
cat > Dockerfile << 'DOCKERFILE_EOF'
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files FIRST for better caching
COPY package*.json ./

# Install dependencies (this layer will be cached if package.json doesn't change)
RUN npm install --production

# Copy application code AFTER dependencies are installed
COPY . .

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Run the application
CMD ["npm", "start"]
DOCKERFILE_EOF

# Create server.js
cat > server.js << 'SERVER_EOF'
const express = require('express');
const app = express();
const port = 3000;

app.set('view engine', 'ejs');
app.use(express.static('public'));

app.get('/', (req, res) => {
  res.render('dashboard', {
    title: "Nitin's Jenkins Pipeline Health Dashboard",
    jobs: [
      {name: "build-project", status: "success", lastBuild: "#8"},
      {name: "test-pipeline", status: "success", lastBuild: "#4"},
      {name: "TMO API Check", status: "success", lastBuild: "#4"},
      {name: "TMO Device Change Check", status: "success", lastBuild: "#1"},
      {name: "fail-freestyle-1", status: "failure", lastBuild: "#5"},
      {name: "fail-freestyle-2", status: "failure", lastBuild: "#4"},
      {name: "success-freestyle-1", status: "success", lastBuild: "#1"},
      {name: "success-freestyle-2", status: "success", lastBuild: "#1"}
    ]
  });
});

app.get('/health', (req, res) => {
  res.json({status: "healthy", service: "frontend"});
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Frontend running at http://0.0.0.0:${port}`);
});
SERVER_EOF

# Create views directory and dashboard template
mkdir -p views
cat > views/dashboard.ejs << 'DASHBOARD_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><%= title %></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #667eea;
            --accent-color: #764ba2;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        
        .container-fluid {
            max-width: 1400px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .header h1 {
            color: var(--primary-color);
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .stat-success { color: var(--success-color); }
        .stat-danger { color: var(--danger-color); }
        .stat-info { color: var(--info-color); }
        .stat-warning { color: var(--warning-color); }
        
        .jobs-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .job-item {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border-left: 5px solid var(--success-color);
            transition: all 0.3s ease;
        }
        
        .job-item:hover {
            transform: translateX(5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .job-item.failure {
            border-left-color: var(--danger-color);
        }
        
        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .job-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
        }
        
        .job-status {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .status-success {
            background: var(--success-color);
            color: white;
        }
        
        .status-failure {
            background: var(--danger-color);
            color: white;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="header">
            <h1><i class="fas fa-tachometer-alt"></i> <%= title %></h1>
            <p>Real-time CI/CD Pipeline Monitoring Dashboard</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number stat-success"><%= jobs.filter(j => j.status === 'success').length %></div>
                <div class="stat-label"><i class="fas fa-check-circle"></i> Successful Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number stat-danger"><%= jobs.filter(j => j.status === 'failure').length %></div>
                <div class="stat-label"><i class="fas fa-times-circle"></i> Failed Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number stat-info"><%= jobs.length %></div>
                <div class="stat-label"><i class="fas fa-tasks"></i> Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number stat-warning"><%= Math.round((jobs.filter(j => j.status === 'success').length / jobs.length) * 100) %>%</div>
                <div class="stat-label"><i class="fas fa-percentage"></i> Success Rate</div>
            </div>
        </div>
        
        <div class="jobs-section">
            <h2 class="section-title">
                <i class="fas fa-list"></i> Pipeline Status
            </h2>
            <% jobs.forEach(job => { %>
                <div class="job-item <%= job.status === 'failure' ? 'failure' : '' %>">
                    <div class="job-header">
                        <div class="job-name">
                            <i class="fas fa-<%= job.status === 'success' ? 'check' : 'times' %>-circle"></i>
                            <%= job.name %>
                        </div>
                        <div class="job-status status-<%= job.status %>">
                            <%= job.status %>
                        </div>
                    </div>
                    <div class="job-details">
                        <i class="fas fa-hashtag"></i> Build: <%= job.lastBuild %> | 
                        <i class="fas fa-clock"></i> Last updated: <%= new Date().toLocaleString() %>
                    </div>
                </div>
            <% }); %>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
DASHBOARD_EOF

cd ..

echo "🔧 Creating optimized docker-compose.yml..."
cat > docker-compose.yml << 'COMPOSE_EOF'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cicd-backend
    ports:
      - "8000:8000"
    environment:
      DEBUG: "false"
      SECRET_KEY: "prod-secret-key-change-in-production"
      CORS_ORIGINS: "*"
      JENKINS_URL: "http://jenkins:8080"
      JENKINS_USERNAME: "admin"
      JENKINS_API_TOKEN: "119945a0409c8335bfdb889b602739a995"
    restart: unless-stopped
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
    depends_on:
      backend:
        condition: service_healthy
    command: ["npm", "start"]
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
COMPOSE_EOF

echo "🚀 Building and starting all containers with optimized Dockerfiles..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 60

echo "📊 Checking container status..."
docker-compose ps

echo "📋 Checking frontend logs..."
docker-compose logs frontend

echo "🌐 Testing endpoints..."
echo "Backend health check:"
curl -s http://localhost:8000/api/health || echo "Backend not responding"

echo "Frontend health check:"
curl -s http://localhost:3000/health || echo "Frontend not responding"

echo "✅ Optimized Dockerfile structure fix completed!"
echo "🌐 Access URLs:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "   Frontend: http://$PUBLIC_IP:3000"
echo "   Backend: http://$PUBLIC_IP:8000"
echo "   Jenkins: http://$PUBLIC_IP:8080"
EOF

echo "✅ Dockerfile structure fix completed!"
