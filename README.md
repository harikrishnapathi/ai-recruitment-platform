# AI Recruitment & Talent Intelligence Platform

Production-oriented full-stack recruitment application with:

- FastAPI + PostgreSQL backend
- React + Vite frontend
- JWT authentication
- Recruiter and candidate accounts
- Job creation and publishing
- Candidate applications
- Resume upload (PDF/DOCX)
- Resume text extraction
- Gemini-powered AI resume analysis
- Skill normalization and job matching
- Recruiter candidate ranking
- Candidate profile management
- Resume deletion and re-analysis
- Alembic database migrations
- Render deployment configuration

## Local development

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set these values in `backend/.env`:

```text
DATABASE_URL=...
JWT_SECRET_KEY=...
GEMINI_API_KEY=...
FRONTEND_URL=http://localhost:5173
SKILL_SEED_KEY=...
```

Run migrations:

```powershell
alembic upgrade head
```

Start API:

```powershell
uvicorn app.main:app --reload
```

Health check:

```text
http://127.0.0.1:8000/api/v1/health
```

### Frontend

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

For local development:

```text
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

## Production deployment on Render

### Backend

Use the root `render.yaml`.

Set:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `GEMINI_API_KEY`
- `FRONTEND_URL`
- `SKILL_SEED_KEY`

The backend build automatically runs:

```text
pip install -r requirements.txt
alembic upgrade head
```

### Frontend

Use `frontend/render.yaml`.

Set:

```text
VITE_API_URL=https://YOUR-BACKEND.onrender.com/api/v1
```

Replace `YOUR-BACKEND` with the actual Render backend hostname.

## Important production security

Never commit `.env` files, API keys, JWT secrets, or uploaded resumes.

The repository intentionally contains only `.env.example` files.

Generate a new strong secret for production and configure it through Render environment variables.

## Main application flow

### Candidate

1. Register as Candidate.
2. Complete profile.
3. Upload PDF/DOCX resume.
4. Click **Run AI Analysis**.
5. AI analysis is persisted to PostgreSQL.
6. Skills are available to the matching engine.
7. Browse published jobs.
8. Apply to jobs.
9. View application status.

### Recruiter

1. Register as Recruiter.
2. Create a job.
3. Add required skills.
4. Publish the job.
5. Review candidates.
6. Candidate matches are recalculated from stored candidate skills and AI resume skills.
7. Open **View Candidate** to see:
   - name
   - email
   - phone
   - location
   - headline
   - current title/company
   - experience
   - resume
   - AI analysis
   - matching skills
   - missing skills
   - match percentage
   - recommendation

## Matching behavior

The matching engine normalizes common aliases such as:

- `py` → `python`
- `python3` → `python`
- `postgres` → `postgresql`
- `fast api` → `fastapi`
- `k8s` → `kubernetes`
- `js` → `javascript`
- `ts` → `typescript`
- `react.js` → `react`
- `nodejs` → `node.js`
- `aws cloud` → `aws`

The score is:

```text
matching required skills / total required skills × 100
```

The match is persisted in `job_matches`.

## Validation performed

The backend Python source has been syntax-compiled with:

```text
python -m compileall app
```

The deliverable excludes:

- `.env` secrets
- generated `dist`
- Python caches
- local uploaded resume files
- local virtual environments
