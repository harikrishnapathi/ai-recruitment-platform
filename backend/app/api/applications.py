import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.application import Application, ApplicationStatus
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus
from app.models.job_match import JobMatch
from app.models.user import User
from app.models.resume import Resume
from app.services.job_matcher import calculate_job_match
from app.models.resume_analysis import ResumeAnalysis


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "/jobs/{job_id}/apply",
    status_code=status.HTTP_201_CREATED,
)
def apply_to_job(
    job_id: uuid.UUID,
    cover_letter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = db.scalar(
        select(Candidate).where(
            Candidate.user_id == current_user.id
        )
    )

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found.",
        )

    job = db.scalar(
        select(Job).where(
            Job.id == job_id
        )
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    if job.status != JobStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Applications are only allowed for published jobs.",
        )

    existing = db.scalar(
        select(Application).where(
            Application.candidate_id == candidate.id,
            Application.job_id == job.id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this job.",
        )

    application = Application(
        candidate_id=candidate.id,
        job_id=job.id,
        status=ApplicationStatus.APPLIED,
        cover_letter=cover_letter,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "id": str(application.id),
        "candidate_id": str(application.candidate_id),
        "job_id": str(application.job_id),
        "status": application.status,
        "cover_letter": application.cover_letter,
        "applied_at": application.applied_at,
        "message": "Application submitted successfully.",
    }


@router.get("/mine")
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == current_user.id))
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")
    rows = db.execute(
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(Application.candidate_id == candidate.id)
        .order_by(Application.applied_at.desc())
    ).all()
    return [
        {
            "id": str(application.id),
            "job_id": str(job.id),
            "job_title": job.title,
            "company": str(job.organization_id),
            "status": application.status,
            "cover_letter": application.cover_letter,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
        }
        for application, job in rows
    ]


@router.get(
    "/jobs/{job_id}",
)
def get_job_applications(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    rows = db.execute(
        select(Application, JobMatch)
        .outerjoin(
            JobMatch,
            (
                JobMatch.job_id == Application.job_id
            )
            & (
                JobMatch.candidate_id
                == Application.candidate_id
            ),
        )
        .where(
            Application.job_id == job.id
        )
        .order_by(
            Application.applied_at.desc()
        )
    ).all()

    return [
        {
            "application_id": str(application.id),
            "candidate_id": str(application.candidate_id),
            "job_id": str(application.job_id),
            "status": application.status,
            "cover_letter": application.cover_letter,
            "applied_at": application.applied_at,
            "match_score": (
                match.match_score
                if match
                else None
            ),
            "matching_skills": (
                match.matching_skills.split(", ")
                if match and match.matching_skills
                else []
            ),
            "missing_skills": (
                match.missing_skills.split(", ")
                if match and match.missing_skills
                else []
            ),
            "recommendation": (
                match.recommendation
                if match
                else None
            ),
        }
        for application, match in rows
    ]

@router.patch("/{application_id}/status")
def update_application_status(
    application_id: uuid.UUID,
    new_status: ApplicationStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.scalar(
        select(Application)
        .join(
            Job,
            Job.id == Application.job_id,
        )
        .where(
            Application.id == application_id,
            Job.created_by == current_user.id,
        )
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    application.status = new_status

    db.commit()
    db.refresh(application)

    return {
        "application_id": str(application.id),
        "candidate_id": str(application.candidate_id),
        "job_id": str(application.job_id),
        "status": application.status,
        "updated_at": application.updated_at,
        "message": "Application status updated successfully.",
    }

@router.get("/{application_id}/candidate")
def get_application_candidate_details(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ==========================================================
    # FIND APPLICATION + JOB + CANDIDATE
    # ==========================================================

    row = db.execute(
        select(Application, Job, Candidate, User)
        .join(
            Job,
            Job.id == Application.job_id,
        )
        .join(
            Candidate,
            Candidate.id == Application.candidate_id,
        )
        .join(
            User,
            User.id == Candidate.user_id,
        )
        .where(
            Application.id == application_id,
            Job.created_by == current_user.id,
        )
    ).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    application, job, candidate, user = row

    # ==========================================================
    # GET LATEST RESUME
    # ==========================================================

    resume = db.scalar(
        select(Resume)
        .where(
            Resume.candidate_id == candidate.id
        )
        .order_by(
            Resume.created_at.desc()
        )
    )

    # ==========================================================
    # GET RESUME ANALYSIS
    # ==========================================================

    analysis = None

    if resume:
        analysis = db.scalar(
            select(ResumeAnalysis)
            .where(
                ResumeAnalysis.resume_id == resume.id
            )
        )

    # ==========================================================
    # GET EXISTING MATCH
    # ==========================================================

    match = db.scalar(
        select(JobMatch).where(
            JobMatch.job_id == job.id,
            JobMatch.candidate_id == candidate.id,
        )
    )

    # ==========================================================
    # ALWAYS RECALCULATE MATCH
    # ==========================================================

    try:
        match_result = calculate_job_match(
            db=db,
            candidate_id=candidate.id,
            job_id=job.id,
        )

        if match:
            # ----------------------------------------------
            # UPDATE EXISTING MATCH
            # ----------------------------------------------

            match.match_score = match_result["match_score"]

            match.matching_skills = ", ".join(
                match_result["matching_skills"]
            )

            match.missing_skills = ", ".join(
                match_result["missing_skills"]
            )

            match.recommendation = (
                match_result["recommendation"]
            )

        else:
            # ----------------------------------------------
            # CREATE NEW MATCH
            # ----------------------------------------------

            match = JobMatch(
                job_id=job.id,
                candidate_id=candidate.id,
                match_score=match_result["match_score"],
                matching_skills=", ".join(
                    match_result["matching_skills"]
                ),
                missing_skills=", ".join(
                    match_result["missing_skills"]
                ),
                recommendation=(
                    match_result["recommendation"]
                ),
            )

            db.add(match)

        db.commit()
        db.refresh(match)

    except ValueError:
        # Matching cannot currently be calculated.
        # Keep Candidate Details page usable.
        match = None

    # ==========================================================
    # RESPONSE
    # ==========================================================

    return {
        "application": {
            "id": str(application.id),
            "status": application.status,
            "cover_letter": application.cover_letter,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
        },

        "job": {
            "id": str(job.id),
            "title": job.title,
        },

        "candidate": {
            "id": str(candidate.id),
            "user_id": str(candidate.user_id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "headline": candidate.headline,
            "phone": candidate.phone,
            "location": candidate.location,
            "total_experience_years": candidate.total_experience_years,
            "current_company": candidate.current_company,
            "current_title": candidate.current_title,
            "bio": candidate.bio,
        },

        "resume": (
            {
                "id": str(resume.id),
                "original_filename": resume.original_filename,
                "file_type": resume.file_type,
                "file_size": resume.file_size,
                "created_at": resume.created_at,
            }
            if resume
            else None
        ),

        "analysis": (
            {
                "id": str(analysis.id),
                "summary": analysis.summary,
                "skills": analysis.skills,
                "experience_years": analysis.experience_years,
                "education": analysis.education,
                "recommended_roles": analysis.recommended_roles,
                "strengths": analysis.strengths,
                "missing_skills": analysis.missing_skills,
            }
            if analysis
            else None
        ),

        "match": (
            {
                "score": match.match_score,

                "matching_skills": (
                    match.matching_skills.split(", ")
                    if match.matching_skills
                    else []
                ),

                "missing_skills": (
                    match.missing_skills.split(", ")
                    if match.missing_skills
                    else []
                ),

                "recommendation": match.recommendation,
            }
            if match
            else None
        ),
    }