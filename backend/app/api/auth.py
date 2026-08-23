from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.dependencies import get_db
from app.models.candidate import Candidate
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.scalar(select(User).where(User.email == request.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
    )
    db.add(user)
    db.flush()

    if request.account_type == "CANDIDATE":
        db.add(Candidate(user_id=user.id))
    else:
        base_slug = f"{request.first_name}-{request.last_name}".lower().replace(" ", "-")
        slug = base_slug
        counter = 1
        while db.scalar(select(Organization).where(Organization.slug == slug)):
            slug = f"{base_slug}-{counter}"
            counter += 1

        organization = Organization(
            name=f"{request.first_name} {request.last_name}'s Organization",
            slug=slug,
        )
        db.add(organization)
        db.flush()
        db.add(
            Membership(
                user_id=user.id,
                organization_id=organization.id,
                role=MembershipRole.OWNER,
            )
        )

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == request.email))

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    membership = db.scalar(select(Membership).where(Membership.user_id == user.id))
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == user.id))

    if membership:
        account_type = "RECRUITER"
        organization_id = str(membership.organization_id)
    elif candidate:
        account_type = "CANDIDATE"
        organization_id = None
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has no recruitment or candidate profile.",
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        organization_id=organization_id,
        account_type=account_type,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )
