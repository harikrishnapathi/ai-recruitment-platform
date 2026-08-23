import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.candidate import Candidate
from app.models.application import Application
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.job_match import JobMatch
from app.services.job_matcher import calculate_job_match
from app.models.user import User
from app.services.resume_analyzer import analyze_resume
from app.services.resume_parser import extract_resume_text


router = APIRouter(
    prefix="/candidates/resumes",
    tags=["Candidate Resumes"],
)


UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_RESUMES_PER_CANDIDATE = 5


def get_candidate(
    current_user: User,
    db: Session,
) -> Candidate:

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

    return candidate


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = get_candidate(
        current_user,
        db,
    )

    original_filename = file.filename or ""

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX resumes are supported.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type.",
        )

    resume_count = len(
        db.scalars(
            select(Resume.id).where(
                Resume.candidate_id == candidate.id
            )
        ).all()
    )

    if resume_count >= MAX_RESUMES_PER_CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"You can store up to "
                f"{MAX_RESUMES_PER_CANDIDATE} resumes. "
                "Delete an old resume before uploading another."
            ),
        )

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume file must be 5 MB or smaller.",
        )

    stored_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = (
        UPLOAD_DIR / stored_filename
    )

    file_path.write_bytes(
        file_content
    )

    try:
        extracted_text = extract_resume_text(
            str(file_path)
        )

    except Exception as exc:

        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Could not extract resume text: {str(exc)}"
            ),
        )

    resume = Resume(
        candidate_id=candidate.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        file_type=file.content_type,
        file_size=len(file_content),
        extracted_text=extracted_text,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "id": str(resume.id),
        "original_filename": resume.original_filename,
        "stored_filename": resume.stored_filename,
        "file_type": resume.file_type,
        "file_size": resume.file_size,
        "message": (
            "Resume uploaded and text extracted successfully."
        ),
    }


@router.get("")
def get_my_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = get_candidate(
        current_user,
        db,
    )

    resumes = db.scalars(
        select(Resume)
        .where(
            Resume.candidate_id == candidate.id
        )
        .order_by(
            Resume.created_at.desc()
        )
    ).all()

    response = []
    for resume in resumes:
        analysis = db.scalar(
            select(ResumeAnalysis).where(
                ResumeAnalysis.resume_id == resume.id
            )
        )

        response.append(
            {
                "id": str(resume.id),
                "original_filename": resume.original_filename,
                "file_type": resume.file_type,
                "file_size": resume.file_size,
                "created_at": resume.created_at,
                "analysis": (
                    {
                        "id": str(analysis.id),
                        "summary": analysis.summary,
                        "skills": analysis.skills or [],
                        "experience_years": analysis.experience_years,
                        "education": analysis.education or [],
                        "recommended_roles": analysis.recommended_roles or [],
                        "strengths": analysis.strengths or [],
                        "missing_skills": analysis.missing_skills or [],
                    }
                    if analysis
                    else None
                ),
            }
        )

    return response


@router.delete("/{resume_id}")
def delete_my_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = get_candidate(
        current_user,
        db,
    )

    resume = db.scalar(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.candidate_id == candidate.id,
        )
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    # Delete AI analysis first.
    analysis = db.scalar(
        select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id == resume.id
        )
    )

    if analysis:
        db.delete(analysis)

    # Delete physical file.
    file_path = Path(
        resume.file_path
    )

    file_path.unlink(
        missing_ok=True
    )

    # Delete database record.
    db.delete(resume)

    db.commit()

    return {
        "resume_id": str(resume_id),
        "message": "Resume deleted successfully.",
    }


@router.post("/{resume_id}/analyze")
def analyze_my_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = get_candidate(
        current_user,
        db,
    )

    resume = db.scalar(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.candidate_id == candidate.id,
        )
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    if not resume.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume does not contain extracted text.",
        )

    try:
        analysis_data = analyze_resume(
            resume.extracted_text
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume AI analysis failed: {str(exc)}",
        )

    # Keep candidate experience synchronized.
    experience_years = analysis_data.get(
        "experience_years"
    )

    if experience_years is not None:
        try:
            candidate.total_experience_years = float(
                experience_years
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

    analysis = db.scalar(
        select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id == resume.id
        )
    )

    if analysis:
        analysis.summary = analysis_data.get(
            "summary",
            "",
        )

        analysis.skills = analysis_data.get(
            "skills",
            [],
        )

        analysis.experience_years = analysis_data.get(
            "experience_years"
        )

        analysis.education = analysis_data.get(
            "education",
            [],
        )

        analysis.recommended_roles = analysis_data.get(
            "recommended_roles",
            [],
        )

        analysis.strengths = analysis_data.get(
            "strengths",
            [],
        )

        analysis.missing_skills = analysis_data.get(
            "missing_skills",
            [],
        )

    else:
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            summary=analysis_data.get(
                "summary",
                "",
            ),
            skills=analysis_data.get(
                "skills",
                [],
            ),
            experience_years=analysis_data.get(
                "experience_years"
            ),
            education=analysis_data.get(
                "education",
                [],
            ),
            recommended_roles=analysis_data.get(
                "recommended_roles",
                [],
            ),
            strengths=analysis_data.get(
                "strengths",
                [],
            ),
            missing_skills=analysis_data.get(
                "missing_skills",
                [],
            ),
        )

        db.add(analysis)

    db.commit()
    db.refresh(analysis)

    # Refresh matches for jobs this candidate has already applied to.
    applications = db.scalars(
        select(Application).where(
            Application.candidate_id == candidate.id
        )
    ).all()

    for application in applications:
        try:
            match_result = calculate_job_match(
                db=db,
                candidate_id=candidate.id,
                job_id=application.job_id,
            )

            existing_match = db.scalar(
                select(JobMatch).where(
                    JobMatch.job_id == application.job_id,
                    JobMatch.candidate_id == candidate.id,
                )
            )

            if existing_match:
                existing_match.match_score = match_result["match_score"]
                existing_match.matching_skills = ", ".join(match_result["matching_skills"])
                existing_match.missing_skills = ", ".join(match_result["missing_skills"])
                existing_match.recommendation = match_result["recommendation"]
            else:
                db.add(
                    JobMatch(
                        job_id=application.job_id,
                        candidate_id=candidate.id,
                        match_score=match_result["match_score"],
                        matching_skills=", ".join(match_result["matching_skills"]),
                        missing_skills=", ".join(match_result["missing_skills"]),
                        recommendation=match_result["recommendation"],
                    )
                )
        except ValueError:
            # A job without required skills should not make resume analysis fail.
            continue

    db.commit()

    return {
        "resume_id": str(resume.id),
        "analysis_id": str(analysis.id),
        "summary": analysis.summary,
        "skills": analysis.skills,
        "experience_years": analysis.experience_years,
        "education": analysis.education,
        "recommended_roles": analysis.recommended_roles,
        "strengths": analysis.strengths,
        "missing_skills": analysis.missing_skills,
        "message": "AI resume analysis completed successfully.",
    }