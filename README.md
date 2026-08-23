# AI Recruitment & Talent Intelligence Platform

An AI-powered recruitment platform that helps recruiters discover and evaluate candidates based on job requirements, skills, experience, and resume content.

The platform provides separate workflows for candidates and recruiters, including resume analysis, job applications, skill-based matching, candidate ranking, and recruitment management.

## Live Demo

Frontend:
https://ai-recruitment-platform-1-8m1v.onrender.com

Backend API:
https://ai-recruitment-platform-prka.onrender.com

API Documentation:
https://ai-recruitment-platform-prka.onrender.com/docs

GitHub:
https://github.com/harikrishnapathi/ai-recruitment-platform

---

## What I Built

I developed this project as a full-stack recruitment platform with an AI-assisted candidate evaluation workflow.

The main idea is simple:

A candidate uploads a resume → the system extracts and analyzes the resume → the candidate applies for jobs → the platform compares candidate skills with job requirements → recruiters can review candidates using match scores and skill differences.

The application has two main user roles:

- Candidate / Job Seeker
- Recruiter / Hiring Team

---

## Key Features

### Candidate

- Candidate registration and login
- JWT-based authentication
- Candidate dashboard
- Resume upload
- PDF and DOCX resume support
- Resume text extraction
- AI resume analysis
- Skill extraction
- Experience extraction
- Education information
- Resume strengths and weaknesses
- Browse published jobs
- Apply for jobs
- Track application status

### Recruiter

- Recruiter registration and login
- Recruiter dashboard
- Create jobs
- Publish jobs
- Archive/delete published jobs
- Define required skills
- Specify required experience for skills
- View applicants
- View candidate details
- Resume information
- Candidate/job matching
- Matching skills
- Missing skills
- Match score
- Candidate recommendations

---

## AI Recruitment Workflow

```text
Candidate Resume
       │
       ▼
Resume Upload
       │
       ▼
Text Extraction
       │
       ▼
AI Resume Analysis
       │
       ├── Skills
       ├── Experience
       ├── Education
       ├── Strengths
       └── Weaknesses
       │
       ▼
Candidate Profile
       │
       ▼
Job Application
       │
       ▼
Job Requirements
       │
       ▼
Candidate / Job Matching
       │
       ├── Matching Skills
       ├── Missing Skills
       ├── Match Score
       └── Recommendation
       │
       ▼
Recruiter Candidate Ranking

Backend Architecture

React Frontend
      │
      │ REST API
      ▼
FastAPI Backend
      │
      ├── Authentication
      ├── Candidate APIs
      ├── Recruiter APIs
      ├── Job APIs
      ├── Application APIs
      ├── Resume APIs
      └── Matching APIs
      │
      ▼
SQLAlchemy
      │
      ▼
PostgreSQL


Authentication

The platform uses JWT-based authentication.

Authentication flow:

User Login
    │
    ▼
FastAPI Authentication API
    │
    ▼
JWT Access Token
    │
    ▼
Frontend stores session
    │
    ▼
Bearer Token
    │
    ▼
Protected API endpoints...



## Tech Stack that i used to built this...

### Frontend
- **React** — Component-based user interface
- **Vite** — Frontend development and production build tooling
- **JavaScript (ES6+)** — Application logic
- **Axios** — Communication between frontend and backend REST APIs
- **CSS3** — Responsive UI styling

### Backend
- **Python** — Core backend language
- **FastAPI** — REST API development and backend services
- **SQLAlchemy** — Database ORM and query management
- **Pydantic** — Request/response validation and data schemas
- **Alembic** — Database migrations
- **JWT** — Authentication and protected API access

### Database
- **PostgreSQL** — Relational database for users, candidates, jobs, applications, skills, resumes and matching data

### AI & Resume Processing
- **AI-powered Resume Analysis** — Extracts candidate information from resume content
- **Resume Text Extraction** — Processes PDF and DOCX resumes
- **Candidate–Job Matching** — Compares candidate skills and experience with job requirements
- **Skill Matching Engine** — Identifies matching and missing skills and generates a match score

### DevOps & Deployment
- **Docker** — Containerized local development environment
- **Docker Compose** — Local PostgreSQL and service orchestration
- **Git & GitHub** — Source control and project collaboration
- **Render** — Production deployment for frontend and backend
- **REST APIs** — Communication between the React frontend and FastAPI backend

### Development Tools
- **VS Code** — Development environment
- **Swagger / OpenAPI** — Interactive backend API documentation
