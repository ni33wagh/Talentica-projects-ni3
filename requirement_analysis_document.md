# 🧠 Requirement Analysis Document

## Key Features
- **CI/CD Health Monitoring Dashboard**
  - Display Jenkins jobs, pipelines, and build results
  - Show metrics such as total pipelines, total builds, success/failure rates, average build time
  - Provide trend analysis (success/failure builds over time)
  - Show failed builds in last 24 hours
  - Node health status of Jenkins controller
- **Integration**
  - Backend service to connect with Jenkins API
  - React-based frontend to visualize builds and metrics
  - Email/SMTP alerts (extendable to Slack/webhooks)
- **Extensibility**
  - Support for additional pipelines (via Jenkins jobs auto-discovery)
  - Compatibility endpoints for legacy UI expectations

## Tech Choices
- **Backend:** FastAPI (Python) with Uvicorn
- **Frontend:** React + Vite + TailwindCSS
- **CI/CD Tool:** Jenkins (REST API integration)
- **Data:** Real-time fetch from Jenkins API; optional persistence via SQLite
- **Deployment:** Docker Compose (backend, frontend, Jenkins service)
- **Monitoring:** Health checks & readiness probes

## APIs / Tools Required
- **Jenkins API** (`/api/json`, job-level APIs)
- **SMTP (Gmail)** for email alerts
- **Curl/Wget** for healthchecks in Docker
- **React libraries:** Chart.js/Recharts for graphs, Lucide icons, shadcn/ui components
- **Containerization:** Docker + Docker Compose
