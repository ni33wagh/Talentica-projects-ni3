#!/bin/bash
# Fix Live Updates on AWS Deployment
# This script updates the AWS deployment to support real-time updates

set -e

echo "🔧 Fixing live updates on AWS deployment..."

# Get the EC2 instance IP from terraform state
INSTANCE_IP=$(grep -A 5 '"public_ip"' /Users/nitinw/Desktop/cicd-health-dashboard/infra/terraform/terraform.tfstate | grep '"value"' | cut -d'"' -f4)

if [ -z "$INSTANCE_IP" ]; then
    echo "❌ Could not find EC2 instance IP from terraform state"
    exit 1
fi

echo "📍 Found EC2 instance IP: $INSTANCE_IP"

# Create the updated docker-compose.yml with full backend
cat > /tmp/docker-compose-fixed.yml << 'EOF'
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
      - SMTP_SERVER=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USERNAME=ni33wagh@gmail.com
      - SMTP_PASSWORD=ztlegvdbfotzxetu
      - FROM_EMAIL=ni33wagh@gmail.com
      - TO_EMAIL=ni33wagh@gmail.com
      - SMTP_USE_TLS=true
    command: >
      bash -c "
        pip install fastapi uvicorn requests python-multipart httpx sqlalchemy pydantic-settings python-socketio &&
        echo 'from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from datetime import datetime
import httpx
import socketio

app = FastAPI(title=\"CI/CD Health Dashboard API\")

# Socket.IO server for real-time updates
sio = socketio.AsyncServer(cors_allowed_origins=\"*\")
sio_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[\"*\"],
    allow_credentials=True,
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

# Jenkins client
jenkins_client = None

class JenkinsClient:
    def __init__(self):
        self.base_url = \"http://jenkins:8080\"
        self.username = \"admin\"
        self.api_token = \"119945a0409c8335bfdb889b602739a995\"
        self._crumb = None
        self._crumb_field = None

    async def get_crumb(self):
        if self._crumb is None:
            try:
                url = f\"{self.base_url}/crumbIssuer/api/json\"
                auth = (self.username, self.api_token)
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, auth=auth, timeout=10.0)
                    if response.status_code == 200:
                        crumb_data = response.json()
                        self._crumb = crumb_data.get(\"crumb\")
                        self._crumb_field = crumb_data.get(\"crumbRequestField\")
            except Exception as e:
                print(f\"Error getting crumb: {e}\")
        return {\"crumb\": self._crumb, \"crumbRequestField\": self._crumb_field}

    async def _make_request(self, endpoint, method=\"GET\", data=None, include_crumb=False):
        url = f\"{self.base_url}{endpoint}\"
        auth = (self.username, self.api_token)
        headers = {\"Content-Type\": \"application/json\"}
        
        if include_crumb and self._crumb and self._crumb_field:
            headers[self._crumb_field] = self._crumb
            
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == \"GET\":
                    response = await client.get(url, auth=auth, headers=headers, timeout=10.0)
                elif method.upper() == \"POST\":
                    response = await client.post(url, auth=auth, headers=headers, json=data, timeout=10.0)
                else:
                    raise ValueError(f\"Unsupported HTTP method: {method}\")

                if response.status_code == 403 and not include_crumb:
                    await self.get_crumb()
                    headers[self._crumb_field] = self._crumb
                    if method.upper() == \"GET\":
                        response = await client.get(url, auth=auth, headers=headers, timeout=10.0)
                    elif method.upper() == \"POST\":
                        response = await client.post(url, auth=auth, headers=headers, json=data, timeout=10.0)

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f\"Jenkins API error: {response.status_code} - {response.text}\")
                    return None
        except Exception as e:
            print(f\"Error making request to {endpoint}: {e}\")
            return None

    async def list_jobs(self):
        result = await self._make_request(\"/api/json?tree=jobs[name,url,color,lastBuild,lastSuccessfulBuild,lastFailedBuild]\")
        if result:
            return result.get(\"jobs\", [])
        return []

    async def list_builds(self, job_name, limit=25):
        result = await self._make_request(f\"/job/{job_name}/api/json?tree=builds[number,url,result,timestamp,duration,executor,description]&limit={limit}\")
        if result:
            return result.get(\"builds\", [])
        return []

# Initialize Jenkins client
jenkins_client = JenkinsClient()

@app.get(\"/\")
async def root():
    return {\"message\": \"CI/CD Health Dashboard API is running!\", \"version\": \"2.0\", \"features\": [\"real-time\", \"jenkins\", \"analytics\"]}

@app.get(\"/api/health\")
async def health():
    return {\"status\": \"healthy\", \"service\": \"backend\", \"timestamp\": datetime.utcnow().isoformat()}

@app.get(\"/api/jobs\")
async def get_jobs():
    try:
        jobs = await jenkins_client.list_jobs()
        return {\"jobs\": jobs}
    except Exception as e:
        return {\"jobs\": [], \"error\": str(e)}

@app.get(\"/api/pipelines\")
async def get_pipelines():
    try:
        jobs = await jenkins_client.list_jobs()
        pipelines = []
        for job in jobs:
            builds = await jenkins_client.list_builds(job[\"name\"], limit=50)
            pipeline = {
                \"name\": job[\"name\"],
                \"url\": job.get(\"url\", \"\"),
                \"color\": job.get(\"color\", \"\"),
                \"status\": job.get(\"color\", \"\"),
                \"info\": {
                    \"builds\": builds
                }
            }
            pipelines.append(pipeline)
        return pipelines
    except Exception as e:
        return {\"pipelines\": [], \"error\": str(e)}

@app.get(\"/api/metrics/overall\")
async def get_overall_metrics():
    try:
        jobs = await jenkins_client.list_jobs()
        total_pipelines = len(jobs)
        total_builds = 0
        successful_jobs = 0
        failed_jobs = 0
        build_times = []
        
        for job in jobs:
            color = job.get(\"color\", \"\")
            last_build = job.get(\"lastBuild\")
            if last_build:
                total_builds += 1
                if last_build.get(\"duration\"):
                    build_times.append(last_build.get(\"duration\", 0) / 1000)
            if \"blue\" in color:
                successful_jobs += 1
            elif \"red\" in color:
                failed_jobs += 1
        
        avg_build_time = sum(build_times) / len(build_times) if build_times else 0
        success_rate = (successful_jobs / total_pipelines * 100) if total_pipelines > 0 else 0
        
        return {
            \"success\": True,
            \"data\": {
                \"metrics\": {
                    \"total_pipelines\": total_pipelines,
                    \"total_builds\": total_builds,
                    \"successful_jobs\": successful_jobs,
                    \"failed_jobs\": failed_jobs,
                    \"avg_build_time\": avg_build_time,
                    \"success_rate\": success_rate
                }
            }
        }
    except Exception as e:
        return {\"success\": False, \"error\": str(e)}

@app.get(\"/api/trigger-collection\")
async def trigger_collection(manual: str = \"0\"):
    try:
        # Trigger data collection and emit real-time update
        await sio.emit(\"pipeline_update\", {\"message\": \"Data collection triggered\", \"timestamp\": datetime.utcnow().isoformat()})
        return {\"status\": \"success\", \"message\": \"Data collection triggered\"}
    except Exception as e:
        return {\"status\": \"error\", \"message\": str(e)}

# Socket.IO events
@sio.event
async def connect(sid, environ):
    print(f\"Client {sid} connected\")
    await sio.emit(\"connect\", {\"message\": \"Connected to CI/CD Dashboard\"}, room=sid)

@sio.event
async def disconnect(sid):
    print(f\"Client {sid} disconnected\")

# Background task for periodic updates
async def periodic_updates():
    while True:
        try:
            # Fetch latest data and emit updates
            jobs = await jenkins_client.list_jobs()
            await sio.emit(\"pipeline_update\", {
                \"jobs\": jobs,
                \"timestamp\": datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f\"Error in periodic updates: {e}\")
        await asyncio.sleep(30)  # Update every 30 seconds

# Start background task
@app.on_event(\"startup\")
async def startup_event():
    asyncio.create_task(periodic_updates())

if __name__ == \"__main__\":
    uvicorn.run(sio_app, host=\"0.0.0.0\", port=8000)
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
      - PUBLIC_BACKEND_URL=http://65.1.251.65:8000
    command: >
      bash -c "
        npm install -g express ejs socket.io-client &&
        echo 'const express = require(\"express\");
const app = express();
const port = 3000;

app.set(\"view engine\", \"ejs\");
app.use(express.static(\"public\"));

// Serve the updated dashboard with real-time features
app.get(\"/\", (req, res) => {
  res.render(\"dashboard\", {
    title: \"Nitin'\''s Jenkins Pipeline Health Dashboard\",
    backendUrl: \"http://65.1.251.65:8000\",
    jobs: [],
    overallMetrics: {},
    jenkinsNodeHealth: null
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
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>CI/CD Pipeline Health Dashboard</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\" rel=\"stylesheet\">
    <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
    <script src=\"https://cdn.socket.io/4.7.2/socket.io.min.js\"></script>
    <script src=\"https://cdn.jsdelivr.net/npm/moment@2.29.4/moment.min.js\"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .kpi-card { background: linear-gradient(45deg, #007bff, #0056b3); color: white; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
        .status-connected { background-color: #28a745; }
        .status-disconnected { background-color: #dc3545; }
        .refresh-btn { background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; }
        .refresh-btn:hover { background: #218838; }
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <h1><%= title %></h1>
            <p>Real-time CI/CD Pipeline Monitoring Dashboard</p>
            <div>
                <span class=\"status-indicator\" id=\"connection-status\"></span>
                <span id=\"connection-text\">Connecting...</span>
                <button class=\"refresh-btn\" onclick=\"refreshData()\">🔄 Refresh</button>
            </div>
        </div>
        
        <div class=\"row\">
            <div class=\"col-md-3\">
                <div class=\"card kpi-card\">
                    <h4 id=\"total-pipelines\">-</h4>
                    <p>Total Pipelines</p>
                </div>
            </div>
            <div class=\"col-md-3\">
                <div class=\"card kpi-card\">
                    <h4 id=\"success-rate\">-</h4>
                    <p>Success Rate</p>
                </div>
            </div>
            <div class=\"col-md-3\">
                <div class=\"card kpi-card\">
                    <h4 id=\"total-builds\">-</h4>
                    <p>Total Builds</p>
                </div>
            </div>
            <div class=\"col-md-3\">
                <div class=\"card kpi-card\">
                    <h4 id=\"avg-build-time\">-</h4>
                    <p>Avg Build Time</p>
                </div>
            </div>
        </div>

        <div class=\"card\">
            <h3>Pipeline Status</h3>
            <div id=\"pipelines-container\">
                <p>Loading pipelines...</p>
            </div>
        </div>

        <div class=\"card\">
            <h3>Real-time Updates</h3>
            <div id=\"updates-log\" style=\"max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;\">
                <p>Waiting for updates...</p>
            </div>
        </div>
    </div>

    <script>
        const backendUrl = \"<%= backendUrl %>\";
        let socket;
        let pipelines = [];
        let metrics = {};

        // Initialize Socket.IO connection
        function initSocket() {
            socket = io(backendUrl, {
                transports: [\"websocket\", \"polling\"],
                withCredentials: true
            });

            socket.on(\"connect\", () => {
                updateConnectionStatus(true);
                addUpdateLog(\"✅ Connected to backend\");
            });

            socket.on(\"disconnect\", () => {
                updateConnectionStatus(false);
                addUpdateLog(\"❌ Disconnected from backend\");
            });

            socket.on(\"pipeline_update\", (data) => {
                addUpdateLog(`📊 Pipeline update: ${JSON.stringify(data).substring(0, 100)}...`);
                if (data.jobs) {
                    updatePipelines(data.jobs);
                }
            });

            socket.on(\"build_update\", (data) => {
                addUpdateLog(`🔨 Build update: ${JSON.stringify(data).substring(0, 100)}...`);
            });
        }

        function updateConnectionStatus(connected) {
            const indicator = document.getElementById(\"connection-status\");
            const text = document.getElementById(\"connection-text\");
            
            if (connected) {
                indicator.className = \"status-indicator status-connected\";
                text.textContent = \"Connected\";
            } else {
                indicator.className = \"status-indicator status-disconnected\";
                text.textContent = \"Disconnected\";
            }
        }

        function addUpdateLog(message) {
            const log = document.getElementById(\"updates-log\");
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement(\"div\");
            logEntry.innerHTML = `<small>[${timestamp}] ${message}</small>`;
            log.appendChild(logEntry);
            log.scrollTop = log.scrollHeight;
        }

        async function refreshData() {
            addUpdateLog(\"🔄 Manual refresh triggered\");
            try {
                const [pipelinesRes, metricsRes] = await Promise.all([
                    fetch(`${backendUrl}/api/pipelines`),
                    fetch(`${backendUrl}/api/metrics/overall`)
                ]);

                if (pipelinesRes.ok) {
                    pipelines = await pipelinesRes.json();
                    updatePipelines(pipelines);
                }

                if (metricsRes.ok) {
                    metrics = await metricsRes.json();
                    updateMetrics(metrics);
                }

                addUpdateLog(\"✅ Data refreshed successfully\");
            } catch (error) {
                addUpdateLog(`❌ Error refreshing data: ${error.message}`);
            }
        }

        function updatePipelines(pipelineData) {
            const container = document.getElementById(\"pipelines-container\");
            if (!pipelineData || pipelineData.length === 0) {
                container.innerHTML = \"<p>No pipelines found</p>\";
                return;
            }

            let html = \"<div class='table-responsive'><table class='table table-striped'><thead><tr><th>Name</th><th>Status</th><th>Last Build</th><th>Builds Count</th></tr></thead><tbody>\";
            
            pipelineData.forEach(pipeline => {
                const status = getStatusFromColor(pipeline.color);
                const buildsCount = pipeline.info && pipeline.info.builds ? pipeline.info.builds.length : 0;
                const lastBuild = pipeline.info && pipeline.info.builds && pipeline.info.builds.length > 0 ? pipeline.info.builds[0] : null;
                
                html += `<tr>
                    <td><strong>${pipeline.name}</strong></td>
                    <td><span class=\"badge bg-${status.color}\">${status.text}</span></td>
                    <td>${lastBuild ? `#${lastBuild.number}` : 'N/A'}</td>
                    <td>${buildsCount}</td>
                </tr>`;
            });
            
            html += \"</tbody></table></div>\";
            container.innerHTML = html;
        }

        function updateMetrics(metricsData) {
            if (metricsData && metricsData.success && metricsData.data && metricsData.data.metrics) {
                const m = metricsData.data.metrics;
                document.getElementById(\"total-pipelines\").textContent = m.total_pipelines || 0;
                document.getElementById(\"success-rate\").textContent = `${(m.success_rate || 0).toFixed(1)}%`;
                document.getElementById(\"total-builds\").textContent = m.total_builds || 0;
                document.getElementById(\"avg-build-time\").textContent = formatDuration(m.avg_build_time || 0);
            }
        }

        function getStatusFromColor(color) {
            if (color.includes(\"blue\")) return { text: \"Success\", color: \"success\" };
            if (color.includes(\"red\")) return { text: \"Failure\", color: \"danger\" };
            if (color.includes(\"yellow\")) return { text: \"In Progress\", color: \"warning\" };
            return { text: \"Unknown\", color: \"secondary\" };
        }

        function formatDuration(seconds) {
            if (!seconds) return \"N/A\";
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            if (minutes > 0) {
                return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
            }
            return `${remainingSeconds.toFixed(1)}s`;
        }

        // Initialize on page load
        document.addEventListener(\"DOMContentLoaded\", () => {
            initSocket();
            refreshData();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        });
    </script>
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

echo "📤 Uploading fixed docker-compose.yml to EC2 instance..."

# Upload the fixed docker-compose.yml to the EC2 instance
scp -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no /tmp/docker-compose-fixed.yml ec2-user@$INSTANCE_IP:/opt/cicd-health-dashboard/docker-compose.yml

echo "🔄 Restarting services on EC2 instance..."

# SSH into the instance and restart the services
ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no ec2-user@$INSTANCE_IP << 'EOF'
cd /opt/cicd-health-dashboard

echo "Stopping existing services..."
docker-compose down

echo "Starting updated services..."
docker-compose up --build -d

echo "Waiting for services to start..."
sleep 30

echo "Checking service status..."
docker-compose ps

echo "Testing backend health..."
curl -f http://localhost:8000/api/health || echo "Backend health check failed"

echo "Testing frontend..."
curl -f http://localhost:3000/health || echo "Frontend health check failed"

echo "✅ Services restarted successfully!"
EOF

echo "🎉 Live updates fix completed!"
echo "📍 Dashboard URL: http://$INSTANCE_IP:3000"
echo "🔧 Backend API: http://$INSTANCE_IP:8000"
echo "📊 Jenkins: http://$INSTANCE_IP:8080"
echo ""
echo "✨ Features now available:"
echo "  - Real-time WebSocket updates"
echo "  - Live Jenkins integration"
echo "  - Auto-refresh every 30 seconds"
echo "  - Manual refresh button"
echo "  - Connection status indicator"
echo "  - Real-time updates log"
