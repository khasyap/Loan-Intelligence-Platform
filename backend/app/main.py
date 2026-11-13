"""
Loan Origination, Risk Assessment & Decision Intelligence Platform
FastAPI REST Application & Web Host
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api.routers import (
    products, applicants, applications, repayments, anomalies, analytics,
    auth, documents, affordability, decisions, disbursements, system_ops, exports
)

app = FastAPI(
    title="Loan Origination & Decision Intelligence Platform",
    description="Enterprise-grade lending origination, affordability assessment, risk decisioning, and repayment amortization REST API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(applicants.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(affordability.router, prefix="/api/v1")
app.include_router(decisions.router, prefix="/api/v1")
app.include_router(repayments.router, prefix="/api/v1")
app.include_router(disbursements.router, prefix="/api/v1")
app.include_router(anomalies.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(system_ops.router, prefix="/api/v1")
app.include_router(exports.router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": "loan-intelligence-backend",
        "version": "1.0.0"
    }

# Mount Frontend production build if available
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", tags=["Frontend SPA"])
    def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path == "health":
            return {"error": "Not Found"}
        target = os.path.join(frontend_dist, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/", tags=["Root"])
    def root_info():
        return {
            "message": "Welcome to the Loan Intelligence Platform API",
            "documentation": "/docs",
            "version": "1.0.0"
        }
