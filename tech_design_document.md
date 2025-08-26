# 🏗️ Tech Design Document

## High-Level Architecture
- **Frontend (React/Vite)**
  - Runs on port 3000
  - Fetches backend API responses
  - Displays dashboards, metrics, charts
- **Backend (FastAPI)**
  - Runs on port 8000
  - Exposes REST API endpoints for Jenkins jobs, metrics, builds
  - Connects to Jenkins server on port 8080
  - Provides health and summary APIs
- **Jenkins (LTS JDK17)**
  - CI/CD server for pipelines
  - Exposed at port 8080
  - Provides job/build metadata via REST API
- **Docker Compose**
  - Orchestrates backend, frontend, Jenkins
  - Provides isolated development stack

## API Structure (Sample Routes & Responses)
- `GET /api/jenkins-node-health` → `{ "status": "UP", "jobs": 4, "jobNames": [...] }`
- `GET /api/metrics/overall` → totals, success/failure counts, avg build time
- `GET /api/metrics/build-trend?windowHours=24` → build trend buckets
- `GET /api/pipelines` → list of pipelines with URLs
- `GET /api/pipelines/{job}/builds?limit=50` → per-job build list
- `GET /api/failed-builds` → failed/unstable builds in last 24h
- `GET /api/dashboard/summary` → aggregated metrics

## Database Schema
*(Optional — only if persistence added via SQLite)*

**Pipelines Table**
```
id | name | url
```

**Builds Table**
```
id | job_name | number | result | duration_ms | timestamp | url
```

**Notifications Table**
```
id | type | message | created_at
```

## UI Layout
- **Top section:** Node Health + Summary Metrics cards
- **Middle section:** Build trend chart (success/failure counts over time)
- **Bottom section:** Failed builds table + Pipeline build details
- **Sidebar/Navigation:** Links to pipelines/jobs
