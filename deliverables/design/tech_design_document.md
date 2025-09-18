# Technical Design Document
## CI/CD Health Dashboard

### Document Information
- **Version**: 1.0
- **Date**: September 2025
- **Author**: AI-Assisted Development
- **Status**: Implementation Complete

---

## 1. High-Level Architecture

### 1.1 System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Jenkins CI    │    │   Backend API   │    │  Frontend UI    │
│                 │    │   (FastAPI)     │    │  (Express.js)   │
│  • Build Jobs   │◄──►│                 │◄──►│                 │
│  • Build Status │    │  • Data Sync    │    │  • Dashboard    │
│  • Build Logs   │    │  • Notifications│    │  • Real-time    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (SQLite)      │
                       │                 │
                       │  • Build Data   │
                       │  • Metrics      │
                       │  • History      │
                       └─────────────────┘
```

### 1.2 Component Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Express.js Server  │  EJS Templates  │  Bootstrap CSS     │
│  • Route Handling   │  • Dynamic UI   │  • Responsive      │
│  • Static Assets    │  • Data Binding │  • Professional    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Layer                            │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Server    │  Services Layer  │  Data Layer        │
│  • API Endpoints   │  • Jenkins Client│  • SQLite DB       │
│  • CORS Middleware │  • Notification  │  • Data Models     │
│  • Error Handling  │  • Metrics Calc  │  • Migrations      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Jenkins API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                          │
├─────────────────────────────────────────────────────────────┤
│  Jenkins Server    │  Gmail SMTP      │  Docker Runtime    │
│  • Build Jobs      │  • Email Alerts  │  • Containerization│
│  • REST API        │  • HTML Templates│  • Orchestration   │
│  • WebSocket       │  • TLS Security  │  • Health Checks   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. API Structure

### 2.1 Backend API Endpoints

#### Core Pipeline Management
```http
GET /api/pipelines
Response: {
  "success": true,
  "data": [
    {
      "name": "build-project",
      "status": "SUCCESS",
      "last_build": {
        "number": 42,
        "duration": 120,
        "timestamp": "2025-09-17T21:30:00Z"
      },
      "health_score": 95
    }
  ]
}

GET /api/pipelines/{pipeline_name}/builds?limit=50
Response: {
  "success": true,
  "data": [
    {
      "build_number": 42,
      "status": "SUCCESS",
      "duration": 120,
      "timestamp": "2025-09-17T21:30:00Z",
      "url": "http://jenkins:8080/job/build-project/42/"
    }
  ]
}
```

#### Metrics and Analytics
```http
GET /api/metrics/overall
Response: {
  "success": true,
  "data": {
    "metrics": {
      "total_pipelines": 14,
      "total_builds": 156,
      "success_rate": 78.5,
      "avg_build_time": 145.2,
      "failed_builds": 34
    }
  }
}

GET /api/analytics/stats
Response: {
  "success": true,
  "data": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "ni33wagh@gmail.com",
    "to_email": "ni33wagh@gmail.com",
    "jenkins_url": "http://localhost:8080"
  }
}
```

#### Jenkins Integration
```http
GET /api/jenkins/jobs
Response: {
  "success": true,
  "data": [
    {
      "name": "build-project",
      "color": "blue",
      "url": "http://localhost:8080/job/build-project/",
      "last_build": {
        "number": 42,
        "url": "http://localhost:8080/job/build-project/42/"
      }
    }
  ]
}

GET /api/jenkins-node-health
Response: {
  "success": true,
  "data": {
    "connection_status": "up",
    "num_jobs": 14,
    "port": 8080,
    "jenkins_url": "http://localhost:8080"
  }
}
```

#### Notification System
```http
POST /api/analytics/notifications/test-email
Request: {
  "job_name": "test-job",
  "build_number": 999,
  "build_url": "http://localhost:8080/job/test-job/999/",
  "failure_reason": "Test failure"
}
Response: {
  "success": true,
  "message": "Test email notification sent successfully"
}
```

### 2.2 Frontend API Integration
```javascript
// Dashboard data fetching
async fetchDashboardData() {
  const [pipelines, metrics, nodeHealth] = await Promise.all([
    fetch('/api/pipelines'),
    fetch('/api/metrics/overall'),
    fetch('/api/jenkins-node-health')
  ]);
  
  return {
    pipelines: await pipelines.json(),
    metrics: await metrics.json(),
    nodeHealth: await nodeHealth.json()
  };
}

// Real-time updates
setInterval(() => {
  this.refreshData();
}, 30000); // 30-second intervals
```

---

## 3. Database Schema

### 3.1 SQLite Database Structure
```sql
-- Builds table for storing build history
CREATE TABLE builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name VARCHAR(255) NOT NULL,
    build_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration INTEGER,
    timestamp DATETIME NOT NULL,
    triggered_by VARCHAR(255),
    branch VARCHAR(255),
    url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pipeline_name, build_number)
);

-- Pipelines table for pipeline metadata
CREATE TABLE pipelines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    health_status VARCHAR(50) DEFAULT 'UNKNOWN',
    build_time_threshold INTEGER DEFAULT 1800,
    notification_channels TEXT DEFAULT '["email"]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table for tracking sent alerts
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name VARCHAR(255) NOT NULL,
    build_number INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    message TEXT
);

-- Metrics table for storing calculated metrics
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name VARCHAR(255) NOT NULL,
    metric_value REAL NOT NULL,
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Data Models (Python/SQLAlchemy)
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Build(Base):
    __tablename__ = 'builds'
    
    id = Column(Integer, primary_key=True)
    pipeline_name = Column(String(255), nullable=False)
    build_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    duration = Column(Integer)
    timestamp = Column(DateTime, nullable=False)
    triggered_by = Column(String(255))
    branch = Column(String(255))
    url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Pipeline(Base):
    __tablename__ = 'pipelines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    health_status = Column(String(50), default='UNKNOWN')
    build_time_threshold = Column(Integer, default=1800)
    notification_channels = Column(Text, default='["email"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    pipeline_name = Column(String(255), nullable=False)
    build_number = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)
```

---

## 4. UI Layout Design

### 4.1 Dashboard Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│                    Top Navigation Bar                       │
│  [Logo] [Dashboard] [Settings] [Refresh] [User] [Status]   │
└─────────────────────────────────────────────────────────────┘
┌─────────┐ ┌─────────────────────────────────────────────────┐
│         │ │                                                 │
│ Sidebar │ │                Main Content Area                │
│         │ │                                                 │
│ • Home  │ │  ┌─────────────────────────────────────────┐   │
│ • Jobs  │ │  │           Hero Section                  │   │
│ • Builds│ │  │    "Nitin's Jenkins Pipeline Health"    │   │
│ • Alerts│ │  └─────────────────────────────────────────┘   │
│ • Stats │ │                                                 │
│         │ │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────┐   │
│         │ │  │   KPI   │ │   KPI   │ │   KPI   │ │ KPI │   │
│         │ │  │  Card   │ │  Card   │ │  Card   │ │Card │   │
│         │ │  └─────────┘ └─────────┘ └─────────┘ └─────┘   │
│         │ │                                                 │
│         │ │  ┌─────────────────────────────────────────┐   │
│         │ │  │            Charts Section               │   │
│         │ │  │  [Build Trends] [Status Distribution]   │   │
│         │ │  └─────────────────────────────────────────┘   │
│         │ │                                                 │
│         │ │  ┌─────────────────────────────────────────┐   │
│         │ │  │           Pipelines Table               │   │
│         │ │  │  [Filter] [Search] [Sort] [Actions]     │   │
│         │ │  └─────────────────────────────────────────┘   │
└─────────┘ └─────────────────────────────────────────────────┘
```

### 4.2 Responsive Design Breakpoints
```css
/* Mobile First Approach */
@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  
  .sidebar {
    position: fixed;
    bottom: 0;
    flex-direction: row;
    height: auto;
  }
  
  .content {
    margin-bottom: 60px;
    padding: 16px;
  }
}

@media (min-width: 769px) and (max-width: 1200px) {
  .layout {
    grid-template-columns: 240px 1fr;
  }
}

@media (min-width: 1201px) {
  .layout {
    grid-template-columns: 260px 1fr;
  }
}
```

### 4.3 Component Hierarchy
```
Dashboard
├── TopBar
│   ├── Logo
│   ├── Navigation
│   ├── Refresh Button
│   └── Status Indicator
├── Sidebar
│   ├── Navigation Menu
│   ├── Quick Stats
│   └── Settings
└── MainContent
    ├── Hero Section
    ├── KPI Cards
    │   ├── Total Pipelines
    │   ├── Success Rate
    │   ├── Average Build Time
    │   └── Failed Builds
    ├── Charts Section
    │   ├── Build Trends Chart
    │   └── Status Distribution
    └── Pipelines Table
        ├── Filter Controls
        ├── Search Bar
        └── Data Table
```

---

## 5. Data Flow Design

### 5.1 Real-time Data Flow
```
Jenkins Build Event
        │
        ▼
┌─────────────────┐
│  Backend Poller │ (30-second intervals)
│  • Fetch Jobs   │
│  • Check Status │
│  • Detect Changes│
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Data Processor │
│  • Parse Data   │
│  • Calculate    │
│  • Store DB     │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Notification   │
│  • Check Rules  │
│  • Send Email   │
│  • Log Event    │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Frontend Update│
│  • Refresh UI   │
│  • Update Charts│
│  • Show Alerts  │
└─────────────────┘
```

### 5.2 Error Handling Flow
```
API Request
    │
    ▼
┌─────────────────┐
│  Try/Catch      │
│  • Validate     │
│  • Process      │
└─────────────────┘
    │
    ▼ (Error)
┌─────────────────┐
│  Error Handler  │
│  • Log Error    │
│  • Return 500   │
│  • Notify User  │
└─────────────────┘
```

---

## 6. Security Design

### 6.1 Authentication & Authorization
```python
# Environment-based configuration
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USERNAME = os.getenv("JENKINS_USERNAME")
JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN")

# CSRF Protection for Jenkins
def get_jenkins_crumb():
    response = requests.get(f"{JENKINS_URL}/crumbIssuer/api/json")
    return response.json()

# Email authentication
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
```

### 6.2 Data Validation
```python
from pydantic import BaseModel, validator

class BuildRequest(BaseModel):
    pipeline_name: str
    build_number: int
    status: str
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['SUCCESS', 'FAILURE', 'ABORTED', 'UNSTABLE']
        if v not in allowed_statuses:
            raise ValueError('Invalid status')
        return v
```

---

## 7. Performance Design

### 7.1 Caching Strategy
```python
# In-memory caching for frequently accessed data
class CacheManager:
    def __init__(self, ttl=300):  # 5 minutes TTL
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            timestamp, data = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None
    
    def set(self, key, data):
        self.cache[key] = (time.time(), data)
```

### 7.2 Database Optimization
```sql
-- Indexes for performance
CREATE INDEX idx_builds_pipeline_status ON builds(pipeline_name, status);
CREATE INDEX idx_builds_timestamp ON builds(timestamp);
CREATE INDEX idx_pipelines_name ON pipelines(name);
CREATE INDEX idx_notifications_pipeline ON notifications(pipeline_name, build_number);
```

---

## 8. Deployment Architecture

### 8.1 Docker Containerization
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### 8.2 Docker Compose Orchestration
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - JENKINS_URL=http://jenkins:8080
      - SMTP_SERVER=smtp.gmail.com
    depends_on: [jenkins]
    
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
    
  jenkins:
    image: jenkins/jenkins:lts-jdk17
    ports: ["8080:8080"]
    volumes: [jenkins_home:/var/jenkins_home]
```

---

*This technical design document provides the complete architectural foundation for the CI/CD Health Dashboard implementation.*
