
# Medical Lab Chatbot (FastAPI + React + Voice)

## What is included
- backend: FastAPI app (backend/main.py)
- frontend: Vite + React app (frontend/)

## Quick local run (developer machine)
### Backend
1. cd backend
2. python -m venv venv && source venv/bin/activate
3. pip install -r requirements.txt
4. uvicorn main:app --reload --host 0.0.0.0 --port 8000

### Frontend
1. cd frontend
2. npm install
3. npm run dev
4. Open http://localhost:5173

The frontend expects the backend at http://localhost:8000 by default. To change, set VITE_API_URL in frontend/.env.

## Deploying to Render
You can deploy backend and frontend as **two separate services** on Render:
- Backend: Python web service (start command: `./start.sh` or `uvicorn main:app --host 0.0.0.0 --port $PORT`)
- Frontend: Static site (build with `npm run build`) or Node service to serve the build.

Alternatively, deploy with Docker by adding Dockerfiles.

