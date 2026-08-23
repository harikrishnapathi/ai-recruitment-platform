import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user import User
from app.services.job_matcher import calculate_job_match


router = APIRouter(
    prefix="/recruiter",
    tags=["Recruiter"],
)


@router.get("/jobs/{job_id}/candidates")
def get_ranked_candidates(
    job_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ==========================================================
    # VERIFY JOB OWNERSHIP
    # ==========================================================

    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.created_by == current_user.id,
        )
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    # ==========================================================
    # GET APPLICATIONS
    # ==========================================================

    rows = db.execute(
        select(
            Candidate,
            Application,
        )
        .join(
            Application,
            Application.candidate_id == Candidate.id,
        )
        .where(
            Application.job_id == job.id
        )
        .order_by(
            Application.applied_at.asc()
        )
        .offset(skip)
        .limit(limit)
    ).all()

    results = []

    # ==========================================================
    # RECALCULATE MATCH FOR EVERY CANDIDATE
    # ==========================================================

    for candidate, application in rows:

        match = db.scalar(
            select(JobMatch).where(
                JobMatch.job_id == job.id,
                JobMatch.candidate_id == candidate.id,
            )
        )

        try:
            result = calculate_job_match(
                db=db,
                candidate_id=candidate.id,
                job_id=job.id,
            )

            if match:
                # ----------------------------------------------
                # UPDATE EXISTING MATCH
                # ----------------------------------------------

                match.match_score = result["match_score"]

                match.matching_skills = ", ".join(
                    result["matching_skills"]
                )

                match.missing_skills = ", ".join(
                    result["missing_skills"]
                )

                match.recommendation = (
                    result["recommendation"]
                )

            else:
                # ----------------------------------------------
                # CREATE MATCH
                # ----------------------------------------------

                match = JobMatch(
                    job_id=job.id,
                    candidate_id=candidate.id,
                    match_score=result["match_score"],
                    matching_skills=", ".join(
                        result["matching_skills"]
                    ),
                    missing_skills=", ".join(
                        result["missing_skills"]
                    ),
                    recommendation=result["recommendation"],
                )

                db.add(match)

            db.commit()
            db.refresh(match)

        except ValueError:
            # Candidate/job cannot currently be matched.
            match = None

        # ======================================================
        # BUILD RESPONSE
        # ======================================================

        results.append(
            {
                "candidate_id": str(candidate.id),
                "application_id": str(application.id),
                "status": application.status,

                "match_score": (
                    match.match_score
                    if match
                    else None
                ),

                "matching_skills": (
                    match.matching_skills.split(", ")
                    if match
                    and match.matching_skills
                    else []
                ),

                "missing_skills": (
                    match.missing_skills.split(", ")
                    if match
                    and match.missing_skills
                    else []
                ),

                "recommendation": (
                    match.recommendation
                    if match
                    else None
                ),

                "applied_at": application.applied_at,
            }
        )

    # ==========================================================
    # SORT BY MATCH SCORE
    # ==========================================================

    results.sort(
        key=lambda item: (
            item["match_score"]
            if item["match_score"] is not None
            else -1
        ),
        reverse=True,
    )

    return results
