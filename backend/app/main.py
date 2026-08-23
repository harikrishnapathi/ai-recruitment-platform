from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.candidates import router as candidate_router
from app.api.skills import router as skills_router, candidate_skills_router
from app.api.resumes import router as resume_router
from app.api.jobs import router as jobs_router
from app.api.applications import router as applications_router
from app.api.dashboard import router as dashboard_router
from app.api.recruiter import router as recruiter_router
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Recruitment & Talent Intelligence Platform",
    version="1.0.0",
    description="AI-powered recruitment SaaS platform",
)

frontend_url = os.getenv("FRONTEND_URL", "").strip()
allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    recruiter_router,
    prefix="/api/v1",
)


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)

app.include_router(
    candidate_router,
    prefix="/api/v1",
)

app.include_router(
    applications_router,
    prefix="/api/v1",
)

app.include_router(skills_router, prefix="/api/v1")
app.include_router(candidate_skills_router, prefix="/api/v1")
app.include_router(
    resume_router,
    prefix="/api/v1",
)

app.include_router(
    jobs_router,
    prefix="/api/v1",
)
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-recruitment-platform",
    }