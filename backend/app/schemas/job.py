from pydantic import BaseModel, Field

from app.models.job import EmploymentType, JobStatus


class JobCreate(BaseModel):
    organization_id: str
    title: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=300)
    description: str = Field(min_length=10)
    department: str | None = None
    location: str | None = None
    is_remote: bool = False
    employment_type: EmploymentType
    experience_min: int | None = Field(default=None, ge=0)
    experience_max: int | None = Field(default=None, ge=0)
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    status: JobStatus = JobStatus.DRAFT


class JobResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    slug: str
    description: str
    department: str | None
    location: str | None
    is_remote: bool
    employment_type: EmploymentType
    experience_min: int | None
    experience_max: int | None
    salary_min: float | None
    salary_max: float | None
    status: JobStatus