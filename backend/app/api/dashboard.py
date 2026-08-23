from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user import User


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/recruiter")
def get_recruiter_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_jobs = db.scalar(
        select(func.count(Job.id)).where(
            Job.created_by == current_user.id
        )
    ) or 0

    published_jobs = db.scalar(
        select(func.count(Job.id)).where(
            Job.created_by == current_user.id,
            Job.status == "PUBLISHED",
        )
    ) or 0

    total_applications = db.scalar(
        select(func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .where(
            Job.created_by == current_user.id
        )
    ) or 0

    shortlisted = db.scalar(
        select(func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .where(
            Job.created_by == current_user.id,
            Application.status == ApplicationStatus.SHORTLISTED,
        )
    ) or 0

    interviews = db.scalar(
        select(func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .where(
            Job.created_by == current_user.id,
            Application.status == ApplicationStatus.INTERVIEW,
        )
    ) or 0

    hired = db.scalar(
        select(func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .where(
            Job.created_by == current_user.id,
            Application.status == ApplicationStatus.HIRED,
        )
    ) or 0

    rejected = db.scalar(
        select(func.count(Application.id))
        .join(Job, Job.id == Application.job_id)
        .where(
            Job.created_by == current_user.id,
            Application.status == ApplicationStatus.REJECTED,
        )
    ) or 0

    average_match_score = db.scalar(
        select(func.avg(JobMatch.match_score))
        .join(Job, Job.id == JobMatch.job_id)
        .where(
            Job.created_by == current_user.id
        )
    )

    return {
        "total_jobs": total_jobs,
        "published_jobs": published_jobs,
        "total_applications": total_applications,
        "shortlisted": shortlisted,
        "interviews": interviews,
        "hired": hired,
        "rejected": rejected,
        "average_match_score": (
            round(float(average_match_score), 2)
            if average_match_score is not None
            else 0
        ),
    }