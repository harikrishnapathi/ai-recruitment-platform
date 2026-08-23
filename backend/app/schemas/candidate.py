from pydantic import BaseModel, Field


class CandidateProfileCreate(BaseModel):
    headline: str | None = Field(
        default=None,
        max_length=255,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    total_experience_years: float = Field(
        default=0,
        ge=0,
        le=60,
    )

    current_company: str | None = Field(
        default=None,
        max_length=255,
    )

    current_title: str | None = Field(
        default=None,
        max_length=255,
    )

    bio: str | None = None


class CandidateProfileUpdate(BaseModel):
    headline: str | None = Field(
        default=None,
        max_length=255,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    total_experience_years: float | None = Field(
        default=None,
        ge=0,
        le=60,
    )

    current_company: str | None = Field(
        default=None,
        max_length=255,
    )

    current_title: str | None = Field(
        default=None,
        max_length=255,
    )

    bio: str | None = None


class CandidateProfileResponse(BaseModel):
    id: str
    user_id: str
    headline: str | None
    phone: str | None
    location: str | None
    total_experience_years: float
    current_company: str | None
    current_title: str | None
    bio: str | None