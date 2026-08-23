import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import RECRUITER_WRITE_ROLES, require_membership
from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.models.user import User
from app.models.application import Application
from app.schemas.job import JobCreate
from app.services.job_matcher import calculate_job_match


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization_id = uuid.UUID(payload.organization_id)
    require_membership(
        db,
        current_user.id,
        organization_id,
        RECRUITER_WRITE_ROLES,
    )

    if payload.experience_min is not None and payload.experience_max is not None and payload.experience_min > payload.experience_max:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum experience cannot exceed maximum experience.")
    if payload.salary_min is not None and payload.salary_max is not None and payload.salary_min > payload.salary_max:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum salary cannot exceed maximum salary.")

    # Check whether slug already exists
    existing_job = db.scalar(
        select(Job).where(
            Job.slug == payload.slug
        )
    )

    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A job with this slug already exists. Please use a different slug.",
        )

    job = Job(
        organization_id=organization_id,
        created_by=current_user.id,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        department=payload.department,
        location=payload.location,
        is_remote=payload.is_remote,
        employment_type=payload.employment_type,
        experience_min=payload.experience_min,
        experience_max=payload.experience_max,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        status=payload.status,
    )

    db.add(job)

    try:
        db.commit()
        db.refresh(job)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A job with this slug already exists. Please use a different slug.",
        )

    return {
        "id": str(job.id),
        "organization_id": str(job.organization_id),
        "title": job.title,
        "slug": job.slug,
        "description": job.description,
        "department": job.department,
        "location": job.location,
        "is_remote": job.is_remote,
        "employment_type": job.employment_type,
        "experience_min": job.experience_min,
        "experience_max": job.experience_max,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "status": job.status,
    }
@router.get("/public")
def get_public_jobs(
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Job).where(Job.status == "PUBLISHED").order_by(Job.created_at.desc())
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            Job.title.ilike(pattern)
            | Job.description.ilike(pattern)
            | Job.department.ilike(pattern)
            | Job.location.ilike(pattern)
        )
    jobs = db.scalars(query).all()
    return [
        {
            "id": str(job.id),
            "title": job.title,
            "slug": job.slug,
            "description": job.description,
            "department": job.department,
            "location": job.location,
            "is_remote": job.is_remote,
            "employment_type": job.employment_type,
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "salary_min": float(job.salary_min) if job.salary_min is not None else None,
            "salary_max": float(job.salary_max) if job.salary_max is not None else None,
            "status": job.status,
            "created_at": job.created_at,
        }
        for job in jobs
    ]


@router.get("/{job_id}")
def get_public_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.status == "PUBLISHED"))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published job not found.")
    skills = db.execute(
        select(Skill, JobSkill).join(JobSkill, JobSkill.skill_id == Skill.id).where(JobSkill.job_id == job.id)
    ).all()
    return {
        "id": str(job.id), "title": job.title, "slug": job.slug, "description": job.description,
        "department": job.department, "location": job.location, "is_remote": job.is_remote,
        "employment_type": job.employment_type, "experience_min": job.experience_min,
        "experience_max": job.experience_max, "salary_min": float(job.salary_min) if job.salary_min is not None else None,
        "salary_max": float(job.salary_max) if job.salary_max is not None else None,
        "status": job.status,
        "skills": [{"id": str(skill.id), "name": skill.name, "category": skill.category, "required_years": js.required_years} for skill, js in skills],
    }


@router.get("")
def get_my_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = db.scalars(
        select(Job)
        .where(
            Job.created_by == current_user.id
        )
        .order_by(
            Job.created_at.desc()
        )
    ).all()

    return [
        {
            "id": str(job.id),
            "title": job.title,
            "slug": job.slug,
            "description": job.description,
            "department": job.department,
            "location": job.location,
            "is_remote": job.is_remote,
            "employment_type": job.employment_type,
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "salary_min": (
                float(job.salary_min)
                if job.salary_min is not None
                else None
            ),
            "salary_max": (
                float(job.salary_max)
                if job.salary_max is not None
                else None
            ),
            "status": job.status,
            "created_at": job.created_at,
        }
        for job in jobs
    ]

@router.post(
    "/{job_id}/skills",
    status_code=status.HTTP_201_CREATED,
)
def add_job_skill(
    job_id: uuid.UUID,
    skill_id: uuid.UUID,
    required_years: int = 0,
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

    skill = db.scalar(
        select(Skill).where(
            Skill.id == skill_id
        )
    )

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    existing = db.scalar(
        select(JobSkill).where(
            JobSkill.job_id == job_id,
            JobSkill.skill_id == skill_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill already added to this job.",
        )

    job_skill = JobSkill(
        job_id=job_id,
        skill_id=skill_id,
        required_years=required_years,
    )

    db.add(job_skill)
    db.commit()
    db.refresh(job_skill)

    return {
        "id": str(job_skill.id),
        "job_id": str(job_skill.job_id),
        "skill_id": str(job_skill.skill_id),
        "skill_name": skill.name,
        "required_years": job_skill.required_years,
    }

@router.get(
    "/{job_id}/skills"
)
def get_job_skills(
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
        select(JobSkill, Skill)
        .join(
            Skill,
            JobSkill.skill_id == Skill.id,
        )
        .where(
            JobSkill.job_id == job.id
        )
        .order_by(
            Skill.name.asc()
        )
    ).all()

    return [
        {
            "id": str(job_skill.id),
            "job_id": str(job_skill.job_id),
            "skill_id": str(skill.id),
            "skill_name": skill.name,
            "category": skill.category,
            "required_years": job_skill.required_years,
        }
        for job_skill, skill in rows
    ]


@router.post("/{job_id}/match")
def match_my_candidate(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
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

    candidate = db.scalar(
        select(Candidate).where(
            Candidate.id == candidate_id
        )
    )

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    application_exists = db.scalar(
        select(Application.id).where(
            Application.job_id == job.id,
            Application.candidate_id == candidate.id,
        )
    )
    if not application_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate has not applied to this job.",
        )

    try:
        result = calculate_job_match(
            db=db,
            candidate_id=candidate.id,
            job_id=job.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Check whether this candidate/job match already exists.
    match = db.scalar(
        select(JobMatch).where(
            JobMatch.job_id == job.id,
            JobMatch.candidate_id == candidate.id,
        )
    )

    if match:
        # Update existing match.
        match.match_score = result["match_score"]
        match.matching_skills = ", ".join(
            result["matching_skills"]
        )
        match.missing_skills = ", ".join(
            result["missing_skills"]
        )
        match.recommendation = result["recommendation"]

    else:
        # Create new match.
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

    return {
        "id": str(match.id),
        "job_id": str(job.id),
        "candidate_id": str(candidate.id),
        **result,
        "message": "Candidate matched successfully.",
    }


@router.get("/{job_id}/matches")
def get_job_matches(
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
        select(JobMatch, Candidate)
        .join(
            Candidate,
            Candidate.id == JobMatch.candidate_id,
        )
        .where(
            JobMatch.job_id == job.id
        )
        .order_by(
            JobMatch.match_score.desc()
        )
    ).all()

    return [
        {
            "id": str(match.id),
            "candidate_id": str(candidate.id),
            "candidate_user_id": str(candidate.user_id),
            "match_score": match.match_score,
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
            "created_at": match.created_at,
        }
        for match, candidate in rows
    ]