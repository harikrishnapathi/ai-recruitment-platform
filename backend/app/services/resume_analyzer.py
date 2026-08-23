import json

from google import genai
from pydantic import BaseModel, Field

from app.core.config import settings


client = genai.Client(api_key=settings.GEMINI_API_KEY)


class ResumeAnalysisResult(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience_years: float = 0
    education: list[str] = Field(default_factory=list)
    recommended_roles: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


def analyze_resume(resume_text: str) -> dict:
    prompt = f"""
You are an AI recruitment assistant.

Analyze the following resume.

Return ONLY valid JSON with exactly these fields:

{{
    "summary": "short professional summary",
    "skills": [],
    "experience_years": 0,
    "education": [],
    "recommended_roles": [],
    "strengths": [],
    "missing_skills": []
}}

Rules:

- skills must be a list of technical and professional skills.
- experience_years must be a number.
- education must be a list of strings.
- recommended_roles must be a list of suitable job titles.
- strengths must be a list of professional strengths.
- missing_skills should contain useful skills the candidate could develop.
- Do not invent employers, degrees, skills, or experience.
- Use only information reasonably supported by the resume.

Resume:

{resume_text}
"""

    response = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string"
                    },
                    "skills": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "experience_years": {
                        "type": "number"
                    },
                    "education": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "recommended_roles": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "strengths": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "missing_skills": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": [
                    "summary",
                    "skills",
                    "experience_years",
                    "education",
                    "recommended_roles",
                    "strengths",
                    "missing_skills"
                ]
            }
        }
    )

    if not response.output_text:
        raise ValueError("Gemini returned an empty response.")

    return json.loads(response.output_text)