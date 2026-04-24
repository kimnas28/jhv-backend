from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
from datetime import datetime, timedelta  # <<< Added for Admin Graph tracking

import os
import httpx
import asyncio
import re
from dotenv import load_dotenv

load_dotenv()

# Imports from your other backend files
from models import UserCreate, UserLogin, JobCreate, AdminCreate, ResumeAnalysisResult
from database import users_collection, jobs_collection, deleted_users_collection # <<< Added deleted_users_collection
from auth import get_password_hash, verify_password, create_access_token
from resume_analyzer import analyze_resume_complete

class PasswordChange(BaseModel):
    email: EmailStr
    current_password: str = Field(..., min_length=6, max_length=128, description="Current password")
    new_password: str = Field(..., min_length=6, max_length=128, description="New password between 6-128 characters")
 
class AccountDelete(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Password for account deletion confirmation")

class ProfileUpdate(BaseModel):
    email: EmailStr
    fullName: str
    phone: str
    location: str
    title: str
    bio: str

class SavedJobItem(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salaryText: str
    applyLink: str
    sourceBoard: str
    type: str = "Full-time"

class AppliedJobItem(BaseModel):
    id: str
    role: str
    company: str
    status: str = "Applied"
    appliedDate: str
    interviewDate: str = ""
    canWithdraw: bool = True

API_KEY = os.getenv("RAPIDAPI_KEY", "")
API_HOST = "jobs-api14.p.rapidapi.com"

async def fetch_board(client, board: str, query: str, location: str):
    url = f"https://{API_HOST}/v2/{board}/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
    }
    params = {"query": query, "location": location}
    try:
        response = await client.get(url, headers=headers, params=params, timeout=10.0)
        response.raise_for_status()
        return {"board": board, "error": False, "data": response.json()}
    except Exception as exc:
        return {"board": board, "error": True, "message": str(exc)}

app = FastAPI(title="HireVia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",       
        "https://jobhirevia.com",      
        "https://www.jobhirevia.com"   
    ],
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/api/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user.model_dump()
    user_dict["password"] = get_password_hash(user_dict["password"])
    user_dict["created_at"] = datetime.utcnow() # <<< Required to track new users for the graph
    
    users_collection.insert_one(user_dict)
    return {"message": "User registered successfully"}

@app.post("/api/register-admin", status_code=status.HTTP_201_CREATED)
async def register_admin(user: AdminCreate):
    if user.admin_secret != "hirevia-admin-2026":
        raise HTTPException(status_code=403, detail="Invalid admin secret passcode")
        
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = {
        "name": user.name, 
        "email": user.email, 
        "role": "admin",
        "password": get_password_hash(user.password),
        "created_at": datetime.utcnow() # <<< Required to track new admins
    }
    
    users_collection.insert_one(user_dict)
    return {"message": "Admin registered successfully"}

@app.post("/api/login")
async def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": db_user["role"]
    }

# ==========================================
# FEATURE ENDPOINTS (Untouched)
# ==========================================

@app.post("/api/analyze-resume")
async def analyze_resume(file: UploadFile = File(...)):
    try:
        filename = file.filename.lower()
        if not filename.endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        available_jobs = []
        analysis_result = analyze_resume_complete(content, filename, available_jobs)
        
        return {
            "status": "success",
            "data": analysis_result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {str(e)}")

@app.post("/api/analyze-resume-with-jobs")
async def analyze_resume_with_jobs(file: UploadFile = File(...), query: str = "developer", location: str = "Philippines"):
    try:
        filename = file.filename.lower()
        if not filename.endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        boards = ["linkedin", "indeed"]
        available_jobs = []
        
        async with httpx.AsyncClient() as client:
            tasks = [fetch_board(client, board, query, location) for board in boards]
            results = await asyncio.gather(*tasks)
        
        for res in results:
            if not res["error"] and res.get("data"):
                data_payload = res["data"]
                jobs_list = []
                
                if isinstance(data_payload, list):
                    jobs_list = data_payload
                elif isinstance(data_payload, dict) and isinstance(data_payload.get("data"), list):
                    jobs_list = data_payload["data"]
                elif isinstance(data_payload, dict) and isinstance(data_payload.get("jobs"), list):
                    jobs_list = data_payload["jobs"]
                
                for job in jobs_list:
                    title = job.get("title") or job.get("jobTitle") or "Job Title Unknown"
                    company = (job.get("company") or job.get("companyName") or job.get("company_name") or 
                              job.get("employer") or job.get("organization") or "Company Unknown")
                    
                    available_jobs.append({
                        "title": title,
                        "job_title": title,
                        "company": company,
                        "company_name": company,
                        "location": job.get("location", location),
                        "description": job.get("description", "") or job.get("jobDescription", ""),
                        "job_description": job.get("description", "") or job.get("jobDescription", ""),
                        "type": job.get("type", "Full-time"),
                        "employment_type": job.get("type", "Full-time"),
                        "required_skills": extract_skills_from_description(job.get("description", "") or job.get("jobDescription", "")),
                        "apply_link": job.get("url") or job.get("applyLink", "#"),
                        "applyLink": job.get("url") or job.get("applyLink", "#"),
                    })
        
        analysis_result = analyze_resume_complete(content, filename, available_jobs)
        
        return {
            "status": "success",
            "data": analysis_result,
            "jobs_analyzed": len(available_jobs)
        }
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {str(e)}")

def extract_skills_from_description(description: str) -> list:
    common_skills = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "django", "flask", "fastapi", "sql", "mongodb", "postgresql",
        "git", "docker", "kubernetes", "aws", "azure", "gcp", "linux", "windows",
        "html", "css", "rest api", "graphql", "communication", "teamwork",
        "leadership", "problem solving", "analytical", "agile", "scrum"
    ]
    description_lower = description.lower()
    found_skills = []
    for skill in common_skills:
        if skill in description_lower:
            found_skills.append(skill.title())
    return found_skills

@app.get("/api/jobs")
async def get_jobs(query: str = "developer", location: str = "Philippines"):
    boards = ["linkedin", "bing", "xing", "indeed"]
    combined_jobs = []

    async with httpx.AsyncClient() as client:
        tasks = [fetch_board(client, board, query, location) for board in boards]
        results = await asyncio.gather(*tasks)

    for res in results:
        if not res["error"] and res.get("data"):
            data_payload = res["data"]
            jobs_list = []

            if isinstance(data_payload, list):
                jobs_list = data_payload
            elif isinstance(data_payload, dict) and isinstance(data_payload.get("data"), list):
                jobs_list = data_payload["data"]
            elif isinstance(data_payload, dict) and isinstance(data_payload.get("jobs"), list):
                jobs_list = data_payload["jobs"]

            for job in jobs_list:
                title = job.get("title") or job.get("jobTitle") or "Job Title Unknown"
                title = re.sub(r"\s*\([a-zA-Z]/[a-zA-Z]/[a-zA-Z]\)", "", title).strip()

                company = (
                    job.get("company") or job.get("companyName") or job.get("company_name")
                    or job.get("employer") or job.get("organization") or "Company Unknown"
                )

                loc = job.get("location") or location
                loc = loc.replace("PH-00", "Philippines").strip()

                salary_text = "Salary not disclosed"
                raw_salary = job.get("salary")
                if raw_salary:
                    if isinstance(raw_salary, dict):
                        s_min = raw_salary.get("min", "")
                        s_max = raw_salary.get("max", "")
                        s_cur = raw_salary.get("currency", "PHP")
                        if s_min or s_max:
                            salary_text = f"{s_cur} {s_min} - {s_max}".strip()
                    else:
                        salary_text = str(raw_salary)
                elif job.get("estimatedSalary"):
                    salary_text = str(job.get("estimatedSalary"))

                link = job.get("url")
                if not link and job.get("jobProviders") and len(job["jobProviders"]) > 0:
                    link = job["jobProviders"][0].get("url")

                combined_jobs.append(
                    {
                        "id": job.get("id", f"{res['board']}-{len(combined_jobs)}"),
                        "title": title,
                        "company": company,
                        "location": loc,
                        "salaryText": salary_text,
                        "applyLink": link or "#",
                        "sourceBoard": res["board"].capitalize(),
                    }
                )

    return {"status": "success", "total_results": len(combined_jobs), "jobs": combined_jobs}

@app.get("/api/jobs/recommended")
async def get_recommended_jobs(location: str = "Philippines"):
    trending_queries = ["software engineer", "data analyst", "frontend developer", "project manager", "customer service"]
    boards = ["linkedin", "indeed"]
    combined_jobs = []
    job_ids_seen = set()

    async with httpx.AsyncClient() as client:
        for query in trending_queries:
            tasks = [fetch_board(client, board, query, location) for board in boards]
            results = await asyncio.gather(*tasks)

            for res in results:
                if not res["error"] and res.get("data"):
                    data_payload = res["data"]
                    jobs_list = []

                    if isinstance(data_payload, list):
                        jobs_list = data_payload
                    elif isinstance(data_payload, dict) and isinstance(data_payload.get("data"), list):
                        jobs_list = data_payload["data"]
                    elif isinstance(data_payload, dict) and isinstance(data_payload.get("jobs"), list):
                        jobs_list = data_payload["jobs"]

                    for job in jobs_list:
                        job_id = job.get("id", f"{res['board']}-{hash(job.get('title', ''))}")
                        if job_id in job_ids_seen:
                            continue
                        job_ids_seen.add(job_id)

                        title = job.get("title") or job.get("jobTitle") or "Job Title Unknown"
                        title = re.sub(r"\s*\([a-zA-Z]/[a-zA-Z]/[a-zA-Z]\)", "", title).strip()

                        company = (job.get("company") or job.get("companyName") or job.get("company_name") or job.get("employer") or job.get("organization") or "Company Unknown")
                        loc = job.get("location") or location
                        loc = loc.replace("PH-00", "Philippines").strip()

                        salary_text = "Salary not disclosed"
                        raw_salary = job.get("salary")
                        if raw_salary:
                            if isinstance(raw_salary, dict):
                                s_min = raw_salary.get("min", "")
                                s_max = raw_salary.get("max", "")
                                s_cur = raw_salary.get("currency", "PHP")
                                if s_min or s_max:
                                    salary_text = f"{s_cur} {s_min} - {s_max}".strip()
                            else:
                                salary_text = str(raw_salary)
                        elif job.get("estimatedSalary"):
                            salary_text = str(job.get("estimatedSalary"))

                        link = job.get("url")
                        if not link and job.get("jobProviders") and len(job["jobProviders"]) > 0:
                            link = job["jobProviders"][0].get("url")

                        combined_jobs.append({
                                "id": job_id, "title": title, "company": company, "location": loc, "salaryText": salary_text, "applyLink": link or "#", "sourceBoard": res["board"].capitalize(),
                        })
                        
                        if len(combined_jobs) >= 10: break
                    if len(combined_jobs) >= 10: break
            if len(combined_jobs) >= 10: break

    return {"status": "success", "total_results": len(combined_jobs), "jobs": combined_jobs[:10]}

# ==========================================
# USER SETTINGS ENDPOINTS (Untouched)
# ==========================================

@app.put("/api/user/change-password")
async def change_password(data: PasswordChange):
    user = users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
 
    if not verify_password(data.current_password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect current password.")
 
    hashed_new_password = get_password_hash(data.new_password)
    users_collection.update_one(
        {"email": data.email},
        {"$set": {"password": hashed_new_password}}
    )
    return {"message": "Password updated successfully"}
 
@app.delete("/api/user/delete-account")
async def delete_account(data: AccountDelete):
    user = users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Account not found.")
 
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password. Deletion cancelled.")
 
    result = users_collection.delete_one({"email": data.email})
    if result.deleted_count > 0:
        return {"message": "Account permanently deleted."}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete account from database.")
    
@app.get("/api/user/profile/{email}")
async def get_profile(email: str):
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database.")
    return {
        "fullName": user.get("name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "location": user.get("location", ""),
        "title": user.get("title", ""),
        "bio": user.get("bio", "")
    }

@app.put("/api/user/profile")
async def update_profile(data: ProfileUpdate):
    user = users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    update_data = {
        "name": data.fullName,
        "phone": data.phone,
        "location": data.location,
        "title": data.title,
        "bio": data.bio
    }
    result = users_collection.update_one(
        {"email": data.email},
        {"$set": update_data}
    )
    return {"message": "Profile updated successfully"}

@app.get("/api/user/{email}/saved-jobs")
async def get_saved_jobs(email: str):
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"saved_jobs": user.get("saved_jobs", [])}

@app.post("/api/user/{email}/saved-jobs")
async def save_job(email: str, job: SavedJobItem):
    result = users_collection.update_one(
        {"email": email},
        {"$addToSet": {"saved_jobs": job.model_dump()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Job saved successfully"}

@app.delete("/api/user/{email}/saved-jobs/{job_id}")
async def remove_saved_job(email: str, job_id: str):
    result = users_collection.update_one(
        {"email": email},
        {"$pull": {"saved_jobs": {"id": job_id}}}
    )
    return {"message": "Job removed successfully"}

@app.get("/api/user/{email}/applied-jobs")
async def get_applied_jobs(email: str):
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"applied_jobs": user.get("applied_jobs", [])}

@app.post("/api/user/{email}/applied-jobs")
async def add_applied_job(email: str, job: AppliedJobItem):
    result = users_collection.update_one(
        {"email": email},
        {"$push": {"applied_jobs": job.model_dump()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Application tracked successfully"}

@app.put("/api/user/{email}/applied-jobs/{job_id}")
async def update_applied_job_status(email: str, job_id: str, payload: dict):
    new_status = payload.get("status", "Withdrawn")
    can_withdraw = payload.get("canWithdraw", False)
    result = users_collection.update_one(
        {"email": email, "applied_jobs.id": job_id},
        {"$set": {
            "applied_jobs.$.status": new_status,
            "applied_jobs.$.canWithdraw": can_withdraw
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application status updated"}

# ==========================================
# NEW ADMIN SYSTEM ENDPOINTS
# ==========================================

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Fetches total counts and 7-day creation/deletion stats"""
    today = datetime.utcnow()
    stats = []
    days_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

    # 1. Generate the 7-day chart data
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        new_count = users_collection.count_documents({
            "created_at": {"$gte": start_of_day, "$lte": end_of_day}
        })

        deleted_count = deleted_users_collection.count_documents({
            "deleted_at": {"$gte": start_of_day, "$lte": end_of_day}
        })

        stats.append({
            "name": days_map[target_date.weekday()],
            "new": new_count,
            "deleted": deleted_count
        })

    # 2. Get the absolute total counts directly from the database for the cards
    total_active_users = users_collection.count_documents({})
    total_deleted_users = deleted_users_collection.count_documents({})

    return {
        "status": "success", 
        "data": stats,
        "total_users": total_active_users,
        "total_deleted": total_deleted_users
    }

@app.get("/api/admin/users")
async def get_all_users():
    """Fetches all registered users for the admin dashboard"""
    users = list(users_collection.find({}, {"password": 0})) # Exclude passwords for security
    for u in users:
        u["_id"] = str(u["_id"])
    return {"users": users}

@app.delete("/api/admin/users/{email}")
async def admin_delete_user(email: str):
    """Deletes a user and logs it for the admin stats graph"""
    user = users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete an admin account.")

    # 1. Log the deletion to track it on the graph
    deleted_users_collection.insert_one({
        "email": user["email"],
        "role": user.get("role", "user"),
        "deleted_at": datetime.utcnow()
    })

    # 2. Delete the user
    users_collection.delete_one({"email": email})
    
    return {"message": "Account permanently deleted."}