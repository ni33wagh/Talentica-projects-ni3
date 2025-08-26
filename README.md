# 🚀 CI/CD Health Dashboard

A monitoring dashboard for Jenkins CI/CD pipelines with a FastAPI backend and React frontend.

---

## ⚙️ Setup & Run Instructions

### Prerequisites
- Docker & Docker Compose
- Git

### Steps
```bash
git clone https://github.com/ni33wagh/Talentica-projects-ni3.git
cd Talentica-projects-ni3

# Build and run services
docker compose up --build
```

- Backend → http://localhost:8000
- Frontend → http://localhost:3000
- Jenkins → http://localhost:8080

### Health Check
```bash
curl http://localhost:8000/api/health
```

---

## 🏗️ Architecture Summary
- **Backend:** FastAPI + Uvicorn
- **Frontend:** React + Vite + TailwindCSS
- **CI/CD:** Jenkins LTS
- **Containerization:** Docker Compose (backend, frontend, Jenkins)
- **Data flow:**  
  Frontend ⇄ Backend ⇄ Jenkins API

---

## 🤖 How AI Tools Were Used
- **ChatGPT / Cursor / Copilot** assisted with:
  - Docker Compose scaffolding
  - FastAPI router design
  - Jenkins API integration
  - Compat shims for legacy routes
  - Prompt engineering and documentation

**Sample prompt:**
```
return me full compat.py with your required changes
```

---

## 📚 Key Learnings & Assumptions
- Jenkins API tokens are required for secure access
- Preemptive Basic Auth needed to bypass CSRF crumb requirement
- Frontend depends heavily on exact route paths → compat shims added
- Failed builds won’t display unless pipeline actually fails
- Assumed Dockerized Jenkins setup for dev/test
