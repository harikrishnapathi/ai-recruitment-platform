from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate import (
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
)


router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


def serialize_candidate(
    candidate: Candidate,
) -> CandidateProfileResponse:
    return CandidateProfileResponse(
        id=str(candidate.id),
        user_id=str(candidate.user_id),
        headline=candidate.headline,
        phone=candidate.phone,
        location=candidate.location,
        total_experience_years=candidate.total_experience_years,
        current_company=candidate.current_company,
        current_title=candidate.current_title,
        bio=candidate.bio,
    )


@router.post(
    "/profile",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_candidate_profile(
    request: CandidateProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_candidate = db.scalar(
        select(Candidate).where(
            Candidate.user_id == current_user.id
        )
    )

    if existing_candidate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate profile already exists.",
        )

    candidate = Candidate(
        user_id=current_user.id,
        headline=request.headline,
        phone=request.phone,
        location=request.location,
        total_experience_years=request.total_experience_years,
        current_company=request.current_company,
        current_title=request.current_title,
        bio=request.bio,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return serialize_candidate(candidate)


@router.get(
    "/profile",
    response_model=CandidateProfileResponse,
)
def get_candidate_profile(
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

    return serialize_candidate(candidate)


@router.patch(
    "/profile",
    response_model=CandidateProfileResponse,
)
def update_candidate_profile(
    request: CandidateProfileUpdate,
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

    update_data = request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)

    return serialize_candidate(candidate)