import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_skill import CandidateSkill
from app.models.job_skill import JobSkill
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.skill import Skill


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {
    "py": "python",
    "python 3": "python",
    "python3": "python",

    "postgres": "postgresql",
    "postgres db": "postgresql",
    "postgres database": "postgresql",
    "postgresql db": "postgresql",
    "postgresql database": "postgresql",

    "fast api": "fastapi",
    "fast-api": "fastapi",

    "k8s": "kubernetes",

    "js": "javascript",
    "javascript es6": "javascript",

    "ts": "typescript",

    "reactjs": "react",
    "react js": "react",
    "react.js": "react",

    "nodejs": "node.js",
    "node js": "node.js",
    "node": "node.js",

    "expressjs": "express",
    "express js": "express",

    "mongo": "mongodb",
    "mongo db": "mongodb",

    "nextjs": "next.js",
    "next js": "next.js",

    "vuejs": "vue",
    "vue js": "vue",

    "docker devops": "docker",

    "aws cloud": "aws",
    "amazon web services": "aws",

    "gcp cloud": "gcp",
    "google cloud platform": "gcp",

    "ms sql": "sql server",
    "mssql": "sql server",

    "rest api": "rest",
    "rest apis": "rest",

    "restful api": "rest",
    "restful apis": "rest",
}


# ============================================================
# NORMALIZE SKILL
# ============================================================

def normalize_skill(value: str) -> str:
    """
    Convert a skill into a predictable comparable format.
    """

    value = str(value or "").strip().lower()

    if not value:
        return ""

    # Replace common separators with spaces
    value = value.replace("_", " ")
    value = value.replace("–", "-")
    value = value.replace("—", "-")

    # Remove common experience suffixes
    # Example:
    # Python - 3 years
    # Python (3 years)
    # Python 3+ years
    value = re.sub(
        r"\(?\s*\d+(?:\.\d+)?\s*\+?\s*years?\s*\)?",
        "",
        value,
    )

    # Remove years/months requirements
    value = re.sub(
        r"\(?\s*\d+(?:\.\d+)?\s*\+?\s*months?\s*\)?",
        "",
        value,
    )

    # Keep useful programming characters
    value = re.sub(
        r"[^a-z0-9+#./\- ]",
        "",
        value,
    )

    # Collapse spaces
    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    # Remove leading/trailing separators
    value = value.strip(" -/.,:")

    if not value:
        return ""

    # Alias conversion
    value = SKILL_ALIASES.get(
        value,
        value,
    )

    return value


# ============================================================
# EXPAND SKILL NAMES
# ============================================================

def expand_skill_names(values) -> list[str]:
    """
    Convert possible comma/semicolon/pipe separated
    values into individual skill names.
    """

    expanded = []

    if not values:
        return expanded

    # Handle a single string
    if isinstance(values, str):
        values = [values]

    for value in values:

        if value is None:
            continue

        # Handle dictionaries safely
        if isinstance(value, dict):

            # Common AI response formats
            for key in (
                "name",
                "skill",
                "title",
            ):
                if key in value:
                    value = value[key]
                    break

        if value is None:
            continue

        parts = re.split(
            r"[,;|]",
            str(value),
        )

        for part in parts:

            part = part.strip()

            if part:
                expanded.append(part)

    return expanded


# ============================================================
# BUILD NORMALIZED SKILL MAP
# ============================================================

def build_skill_map(skill_names):
    """
    Create:

        normalized skill -> original display name
    """

    skill_map = {}

    for name in expand_skill_names(skill_names):

        normalized = normalize_skill(name)

        if not normalized:
            continue

        skill_map.setdefault(
            normalized,
            name.strip(),
        )

    return skill_map


# ============================================================
# COMPARE SKILLS
# ============================================================

def skills_match(
    required_skill: str,
    candidate_skill: str,
) -> bool:
    """
    Compare two normalized skills.

    Exact matching is preferred.

    A small amount of controlled fuzzy matching is
    allowed for things such as:

        python vs python programming
        django vs django framework
        react vs react framework
    """

    required = normalize_skill(
        required_skill
    )

    candidate = normalize_skill(
        candidate_skill
    )

    if not required or not candidate:
        return False

    # Exact match
    if required == candidate:
        return True

    # Candidate contains required skill
    # Example:
    # "python programming" contains "python"
    if (
        len(required) >= 4
        and required in candidate
    ):
        return True

    # Required contains candidate skill
    if (
        len(candidate) >= 4
        and candidate in required
    ):
        return True

    return False


# ============================================================
# CALCULATE JOB MATCH
# ============================================================

def calculate_job_match(
    db: Session,
    candidate_id,
    job_id,
):
    # ========================================================
    # JOB REQUIRED SKILLS
    # ========================================================

    job_rows = db.execute(
        select(
            JobSkill,
            Skill,
        )
        .join(
            Skill,
            Skill.id == JobSkill.skill_id,
        )
        .where(
            JobSkill.job_id == job_id
        )
    ).all()

    if not job_rows:
        raise ValueError(
            "This job has no required skills."
        )

    required_skill_names = []

    for _, skill in job_rows:

        if not skill or not skill.name:
            continue

        required_skill_names.extend(
            expand_skill_names(
                [skill.name]
            )
        )

    required_skill_map = build_skill_map(
        required_skill_names
    )

    if not required_skill_map:
        raise ValueError(
            "This job has no valid required skills."
        )

    # ========================================================
    # EXPLICIT CANDIDATE SKILLS
    # ========================================================

    candidate_skill_rows = db.execute(
        select(
            Skill.name
        )
        .join(
            CandidateSkill,
            CandidateSkill.skill_id == Skill.id,
        )
        .where(
            CandidateSkill.candidate_id
            == candidate_id
        )
    ).all()

    explicit_skill_names = [
        row[0]
        for row in candidate_skill_rows
        if row[0]
    ]

    # ========================================================
    # AI RESUME ANALYSIS
    # ========================================================

    analysis_rows = db.execute(
        select(
            ResumeAnalysis,
        )
        .join(
            Resume,
            Resume.id == ResumeAnalysis.resume_id,
        )
        .where(
            Resume.candidate_id == candidate_id
        )
        .order_by(
            Resume.created_at.desc()
        )
    ).scalars().all()

    analyzed_skill_names = []

    # Look through analyses until we find usable skills.
    for analysis in analysis_rows:

        if not analysis:
            continue

        skills = getattr(
            analysis,
            "skills",
            None,
        )

        if not skills:
            continue

        # JSON/list response
        if isinstance(skills, list):

            analyzed_skill_names = [
                str(skill).strip()
                for skill in skills
                if skill
            ]

        # JSON string response
        elif isinstance(skills, str):

            analyzed_skill_names = (
                expand_skill_names(skills)
            )

        # Other iterable/dict response
        elif isinstance(skills, dict):

            analyzed_skill_names = (
                expand_skill_names(skills)
            )

        if analyzed_skill_names:
            break

    # ========================================================
    # COMBINE CANDIDATE SKILLS
    # ========================================================

    candidate_skill_names = (
        explicit_skill_names
        + analyzed_skill_names
    )

    candidate_skill_map = build_skill_map(
        candidate_skill_names
    )

    # ========================================================
    # CALCULATE MATCH
    # ========================================================

    matching_skills = []
    missing_skills = []

    for (
        normalized_required,
        display_name,
    ) in required_skill_map.items():

        matched = False

        # First try normalized exact match
        if normalized_required in candidate_skill_map:
            matched = True

        # Then controlled comparison
        if not matched:

            for candidate_normalized in (
                candidate_skill_map.keys()
            ):

                if skills_match(
                    normalized_required,
                    candidate_normalized,
                ):
                    matched = True
                    break

        if matched:

            matching_skills.append(
                display_name
            )

        else:

            missing_skills.append(
                display_name
            )

    # ========================================================
    # SCORE
    # ========================================================

    total_required = len(
        required_skill_map
    )

    total_matching = len(
        matching_skills
    )

    if total_required == 0:
        match_score = 0
    else:
        match_score = round(
            (
                total_matching
                / total_required
            )
            * 100
        )

    # Keep score safely between 0 and 100
    match_score = max(
        0,
        min(
            100,
            match_score,
        ),
    )

    # ========================================================
    # RECOMMENDATION
    # ========================================================

    if match_score >= 80:

        recommendation = (
            "Strong match"
        )

    elif match_score >= 60:

        recommendation = (
            "Good match"
        )

    elif match_score >= 40:

        recommendation = (
            "Partial match"
        )

    else:

        recommendation = (
            "Weak match"
        )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "match_score": match_score,

        "matching_skills":
            matching_skills,

        "missing_skills":
            missing_skills,

        "recommendation":
            recommendation,
    }