from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)


class SkillResponse(BaseModel):
    id: str
    name: str
    category: str | None


class CandidateSkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    years_of_experience: float = Field(
        default=0,
        ge=0,
        le=60,
    )
    proficiency_level: str = Field(
        default="INTERMEDIATE",
        max_length=50,
    )


class CandidateSkillResponse(BaseModel):
    id: str
    skill_id: str
    skill_name: str
    category: str | None
    years_of_experience: float
    proficiency_level: str