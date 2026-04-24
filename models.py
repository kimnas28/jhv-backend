from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Password between 6-128 characters")
    role: str # "jobseeker" or "employer"

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Password between 6-128 characters")
    admin_secret: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Password between 6-128 characters")

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class JobCreate(BaseModel):
    title: str
    description: str
    location: str
    type: str
    employer_id: str


class Education(BaseModel):
    degree: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None


class WorkExperience(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: Optional[list] = None


class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CandidateProfile(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    education: Optional[list[Education]] = None
    work_experience: Optional[list[WorkExperience]] = None
    skills: Optional[list[str]] = None
    certifications: Optional[list[str]] = None
    projects: Optional[list[Project]] = None
    summary: Optional[str] = None


class SkillAnalysis(BaseModel):
    technical_skills: Optional[list[str]] = None
    soft_skills: Optional[list[str]] = None
    skill_levels: Optional[dict] = None


class MatchedJob(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    match_score: Optional[float] = None
    reason_for_match: Optional[str] = None
    matched_skills: Optional[list[str]] = None
    missing_skills: Optional[list[str]] = None
    apply_link: Optional[str] = None


class ResumeAnalysisResult(BaseModel):
    candidate_profile: CandidateProfile
    skill_analysis: SkillAnalysis
    job_recommendations: Optional[list[MatchedJob]] = None
    improvement_suggestions: Optional[list[str]] = None
    extracted_text: Optional[str] = None