from app.services.resume_analyzer import analyze_resume


sample_resume = """
Harikrishna Pathi

Python Backend Developer

Skills:
Python, FastAPI, Django, PostgreSQL, Redis, Docker, AWS

Experience:
3 years of experience developing backend APIs and web applications.

Education:
B.Tech in Electronics and Communication Engineering.

Built REST APIs using Python and FastAPI.
Worked with PostgreSQL and Redis.
Used Docker for application deployment.
"""


result = analyze_resume(sample_resume)

print("\n========== AI RESUME ANALYSIS ==========\n")
print(result)

print("\n=========================================")