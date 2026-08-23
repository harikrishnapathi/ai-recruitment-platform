from sqlalchemy import select

from app.db.dependencies import get_db
from app.models.skill import Skill


SKILLS = [
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


def seed_skills():
    db = next(get_db())

    try:
        added = 0

        for name, category in SKILLS:
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

        print(f"Skills added: {added}")
        print(f"Total skills available: {len(SKILLS)}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_skills()