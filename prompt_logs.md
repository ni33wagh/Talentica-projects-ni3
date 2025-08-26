# CI/CD Health Dashboard – Prompt Logs

This document tracks the exact prompts used during the creation and setup of the **CI/CD Health Dashboard** project.

---

## 1. Environment Setup
- *Prompt:*  
  *"provide a complete ready-to-run .env, docker-compose.yml, and frontend Dockerfile setup that guarantees both backend and frontend come up correctly with the live dashboard. but also make sure frontend will fetch the data from backend so there has to be communication between both frontend & backend"*

---

## 2. Jenkins Integration
- *Prompt:*  
  *"how to get JENKINS_API_TOKEN"*

- *Prompt:*  
  *"where is that generate api token option in this?"*

- *Prompt:*  
  *"now its asking password & username but it didn't allow to create user"*

- *Prompt:*  
  *"so do the required change in it & return me full .yml file back"*

---

## 3. Backend Endpoints
- *Prompt:*  
  *"means which file should I edit – Create the router file inside the backend container"*

- *Prompt:*  
  *"return me full compat.py with your required changes"*

---

## 4. Debugging & Fixes
- *Prompt:*  
  *"docker compose logs -f backend → got SyntaxError, fix dashboard.py/compat.py import error"*

- *Prompt:*  
  *"now frontend dashboard is getting update but only Total pipelines are getting update but not other things, do we have to create those things in backend?"*

- *Prompt:*  
  *"can we use anything from routers.zip in our application"*

- *Prompt:*  
  *"can you go through this file & check whats difference between it & our application"*

---

## 5. Styling / Frontend
- *Prompt:*  
  *"i want change color of all icons or titles"*

- *Prompt:*  
  *"i don't see src, can you give me exact location of it?"*

---

## 6. Final Request
- *Prompt:*  
  *"can you create on prompt_logs.md which will contain all the prompts i have used to create cicd-health-dashboard also print once to review"*
