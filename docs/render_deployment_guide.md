# Render.com Deployment Guide — Loan Intelligence Platform

This guide outlines how to deploy the **Loan Intelligence Platform** on [Render.com](https://render.com) using either the **Native Python Runtime** or the **Multi-Stage Docker Container**.

---

## 1. Architecture Overview on Render

The Loan Intelligence Platform is designed to run efficiently on Render as a **single unified web service**:
- **Backend**: FastAPI REST API running on Uvicorn, serving endpoints under `/api/v1` and health checks at `/health`.
- **Frontend**: React 18 + TypeScript + Vite Single-Page Application (SPA) built to static assets (`frontend/dist`) and mounted directly by FastAPI.
- **Port Binding**: Dynamically reads Render's assigned `$PORT` environment variable (`--host 0.0.0.0 --port $PORT`).
- **Database**: Default production SQLite (`loan_platform.db`) or managed Render PostgreSQL via the `DATABASE_URL` environment variable.

```mermaid
flowchart LR
    Client([End Users / Browsers]) -->|HTTPS:443| RenderLB[Render Cloud Load Balancer]
    RenderLB -->|HTTP:$PORT| Uvicorn[FastAPI / Uvicorn Server]
    
    subgraph Single Render Web Service
        Uvicorn -->|Mount /assets| FrontendStatic[Static SPA Assets - frontend/dist]
        Uvicorn -->|Route /api/v1| APIRouters[FastAPI Routers]
        APIRouters --> BusinessLogic[Deterministic Decision & Risk Engine]
        APIRouters --> ExportEngine[Excel / CSV / PDF Export Engine]
    end
    
    BusinessLogic --> DB[(SQLite / Render PostgreSQL)]
```

---

## 2. Option A: One-Click Blueprint Deployment (Recommended)

1. **Push your code to GitHub / GitLab**.
2. Log in to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** > **Blueprint**.
4. Connect your repository.
5. Render detects `render.yaml` automatically.
6. Click **Apply**.
7. Render will execute `render-build.sh`, compile the React frontend, set up Python dependencies, bind to `$PORT`, and bring the service live with free SSL.

---

## 3. Option B: Manual Web Service Setup (Native Python)

If you configure the Web Service manually via the Render UI:

| Setting | Value |
| :--- | :--- |
| **Name** | `loan-intelligence-platform` |
| **Region** | `Oregon (US West)` or your preferred region |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `./render-build.sh` |
| **Start Command** | `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path**| `/health` |

### Required Environment Variables:

| Variable | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Locks Python version |
| `NODE_VERSION` | `20.12.0` | Enables Node.js in build environment |
| `ENVIRONMENT` | `production` | Enables production mode |
| `SECRET_KEY` | *(Click Generate)* | JWT authentication encryption key |
| `DATABASE_URL` | `sqlite:///./loan_platform.db` | Operational database path |

---

## 4. Option C: Docker Container Deployment

If deploying via Docker on Render:

1. Click **New +** > **Web Service**.
2. Select your repository.
3. Choose **Docker** as the Runtime.
4. Render detects the root `Dockerfile`.
5. The multi-stage `Dockerfile` handles building the React frontend (`node:20-alpine`) and installing Python requirements (`python:3.11-slim`), starting with:
   ```sh
   sh -c "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
   ```
6. Render's dynamic `$PORT` is automatically passed into the container.

---

## 5. PostgreSQL Database Migration (Optional)

To switch from the default SQLite database to a Render Managed PostgreSQL instance:

1. In Render Dashboard, click **New +** > **PostgreSQL**.
2. Name the database `loan_origination_db`.
3. Copy the **Internal Database URL** provided by Render.
4. In your Web Service **Environment**, set:
   ```
   DATABASE_URL = postgresql://user:password@hostname:5432/loan_origination_db
   ```
5. Run the migration script or baseline generator:
   ```sh
   python generator/generate.py --profile starter
   ```

---

## 6. Verification and Health Checks

Once deployed, verify your instance:
- **Web App**: `https://<your-subdomain>.onrender.com/`
- **Swagger Documentation**: `https://<your-subdomain>.onrender.com/docs`
- **Health Check**: `https://<your-subdomain>.onrender.com/health` (Returns `{"status": "HEALTHY", ...}`)
- **CSV / Excel / PDF Exports**: Click **Export Portfolio** on the Executive Suite to verify downloadable reports.
