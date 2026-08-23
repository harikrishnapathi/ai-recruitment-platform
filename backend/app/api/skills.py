import uuid
import os



from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import CandidateSkillCreate, CandidateSkillResponse

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("")
def list_skills(db: Session = Depends(get_db)):
    skills = db.scalars(select(Skill).order_by(Skill.name.asc())).all()
    return [
        {"id": str(skill.id), "name": skill.name, "category": skill.category}
        for skill in skills
    ]


candidate_skills_router = APIRouter(prefix="/candidates/skills", tags=["Candidate Skills"])


@candidate_skills_router.post("", response_model=CandidateSkillResponse, status_code=status.HTTP_201_CREATED)
def add_candidate_skill(
    request: CandidateSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == current_user.id))
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")
    skill_name = request.skill_name.strip()
    if not skill_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill name is required.")
    skill = db.scalar(select(Skill).where(Skill.name.ilike(skill_name)))
    if not skill:
        skill = Skill(name=skill_name, category=request.category)
        db.add(skill)
        db.flush()
    existing = db.scalar(select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id, CandidateSkill.skill_id == skill.id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate already has this skill.")
    candidate_skill = CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, years_of_experience=request.years_of_experience, proficiency_level=request.proficiency_level)
    db.add(candidate_skill)
    db.commit()
    db.refresh(candidate_skill)
    return CandidateSkillResponse(id=str(candidate_skill.id), skill_id=str(skill.id), skill_name=skill.name, category=skill.category, years_of_experience=candidate_skill.years_of_experience, proficiency_level=candidate_skill.proficiency_level)


@candidate_skills_router.get("", response_model=list[CandidateSkillResponse])
def get_candidate_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == current_user.id))
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")
    rows = db.execute(select(CandidateSkill, Skill).join(Skill, CandidateSkill.skill_id == Skill.id).where(CandidateSkill.candidate_id == candidate.id)).all()
    return [CandidateSkillResponse(id=str(cs.id), skill_id=str(skill.id), skill_name=skill.name, category=skill.category, years_of_experience=cs.years_of_experience, proficiency_level=cs.proficiency_level) for cs, skill in rows]


@candidate_skills_router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate_skill(skill_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == current_user.id))
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")
    candidate_skill = db.scalar(select(CandidateSkill).where(CandidateSkill.id == skill_id, CandidateSkill.candidate_id == candidate.id))
    if not candidate_skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate skill not found.")
    db.delete(candidate_skill)
    db.commit()
   

@router.post("/seed")
def seed_skills(
    x_seed_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    expected_key = os.getenv("SKILL_SEED_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SKILL_SEED_KEY is not configured.",
        )

    if x_seed_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid seed key.",
        )

    seed_data = [
        ("Python", "Programming"),
        ("JavaScript", "Programming"),
        ("TypeScript", "Programming"),
        ("Java", "Programming"),
        ("C++", "Programming"),
        ("C#", "Programming"),
        ("Go", "Programming"),
        ("Rust", "Programming"),
        ("PHP", "Programming"),
        ("Ruby", "Programming"),
        ("FastAPI", "Backend Framework"),
        ("Django", "Backend Framework"),
        ("Flask", "Backend Framework"),
        ("Spring Boot", "Backend Framework"),
        ("Node.js", "Backend"),
        ("Express.js", "Backend"),
        ("React", "Frontend"),
        ("Vue.js", "Frontend"),
        ("Angular", "Frontend"),
        ("HTML5", "Frontend"),
        ("CSS3", "Frontend"),
        ("Tailwind CSS", "Frontend"),
        ("PostgreSQL", "Database"),
        ("MySQL", "Database"),
        ("MongoDB", "Database"),
        ("Redis", "Database"),
        ("Docker", "DevOps"),
        ("Kubernetes", "DevOps"),
        ("AWS", "Cloud"),
        ("Azure", "Cloud"),
        ("Google Cloud", "Cloud"),
        ("Git", "Tools"),
        ("GitHub", "Tools"),
        ("GitHub Actions", "DevOps"),
        ("REST APIs", "Backend"),
        ("GraphQL", "Backend"),
        ("WebSockets", "Backend"),
        ("JWT", "Authentication"),
        ("Machine Learning", "AI/ML"),
        ("Artificial Intelligence", "AI/ML"),
        ("Generative AI", "AI/ML"),
        ("LangChain", "AI/ML"),
        ("OpenAI", "AI/ML"),
    ]

    added = 0

    for name, category in seed_data:
        existing = db.scalar(
            select(Skill).where(
                Skill.name.ilike(name)
            )
        )

        if existing:
            continue

        db.add(
            Skill(
                name=name,
                category=category,
            )
        )
        added += 1

    db.commit()

    total = db.scalar(
    select(func.count()).select_from(Skill)
)
    return {
        "message": "Skills seeded successfully.",
        "added": added,
        "total": total,
    }
__all__ = ["router", "candidate_skills_router"]
