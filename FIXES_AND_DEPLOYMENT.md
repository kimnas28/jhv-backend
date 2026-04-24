# Backend 500 Error Fixes - Complete Deployment Guide

## Summary of Fixes Applied

### 1. ✅ Requirements.txt - Explicit bcrypt Version
**File**: `requirements.txt`
**Change**: Added explicit `bcrypt==4.0.1`
**Reason**: Passlib needs explicit bcrypt version to avoid `AttributeError: module 'bcrypt' has no attribute 'about'`

```
bcrypt==4.0.1  # Added for passlib compatibility
```

---

### 2. ✅ auth.py - Password Truncation for 72-byte Limit
**File**: `auth.py`
**Changes**:
- Added `_truncate_password()` helper function
- Updated `get_password_hash()` to truncate before hashing
- Updated `verify_password()` to truncate before verification

**Why This Matters**:
- Bcrypt has a hard 72-byte limit per password
- Without consistent truncation, registration and login use different password inputs
- This causes authentication mismatches ("Invalid password")

```python
def _truncate_password(password: str) -> str:
    """Truncate password to 72 bytes (bcrypt's limit)."""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes.decode('utf-8', errors='ignore')
```

---

### 3. ✅ models.py - Pydantic Password Validation
**File**: `models.py`
**Changes**: Added `Field()` constraints to password fields in:
- `UserCreate`: `password` field now has `min_length=6, max_length=128`
- `AdminCreate`: `password` field now has `min_length=6, max_length=128`
- `UserLogin`: `password` field now has `min_length=6, max_length=128`

**Why This Matters**:
- FastAPI validates request before handler executes
- Prevents invalid payloads from reaching password hashing
- Provides clear error messages to frontend (400 Bad Request, not 500)

```python
password: str = Field(..., min_length=6, max_length=128, 
    description="Password between 6-128 characters")
```

---

### 4. ✅ main.py - Password Validation in API Models
**File**: `main.py`
**Changes**: Updated password fields in:
- `PasswordChange`: Both `current_password` and `new_password` validated
- `AccountDelete`: `password` field validated

---

### 5. ✅ CORS Configuration - Already Correct
**File**: `main.py` (lines 77-85)
**Status**: ✅ No changes needed
- Includes both `https://jobhirevia.com` and `https://www.jobhirevia.com`
- Credentials, methods, and headers properly configured

---

## Deployment Checklist

### Phase 1: Local Validation (Dev Environment)

- [ ] **Reinstall Dependencies**
  ```bash
  pip install --upgrade pip
  rm -r venv/  # or your virtual environment folder
  python -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

- [ ] **Verify Bcrypt Installation**
  ```bash
  python -c "import bcrypt; print(bcrypt.__version__)"
  # Should output: 4.0.1
  ```

- [ ] **Verify Passlib Configuration**
  ```bash
  python -c "from passlib.context import CryptContext; pwd = CryptContext(schemes=['bcrypt']); print('OK')"
  ```

- [ ] **Test Locally (if possible)**
  ```bash
  python main.py
  # Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```

### Phase 2: Manual API Testing (Before Frontend)

**Using FastAPI /docs Endpoint**:

1. **Navigate to API Documentation**
   ```
   http://localhost:8000/docs  (locally)
   https://jhv-backend-production.up.railway.app/docs  (production)
   ```

2. **Test 1: Register with Valid Password (Short)**
   ```json
   POST /api/register
   {
     "name": "Test User",
     "email": "test@example.com",
     "password": "TestPass123",
     "role": "jobseeker"
   }
   ```
   ✅ Expected: 201 Created with `"message": "User registered successfully"`

3. **Test 2: Register with Password Near 72-byte Limit**
   ```json
   POST /api/register
   {
     "name": "Test User 2",
     "email": "test2@example.com",
     "password": "VerylongpasswordWith123!@#SpecialChars$%^&*()VerylongpasswordWith123!@#",
     "role": "jobseeker"
   }
   ```
   ✅ Expected: 201 Created (password truncated safely by bcrypt)

4. **Test 3: Login with Same Credentials**
   ```json
   POST /api/login
   {
     "email": "test@example.com",
     "password": "TestPass123"
   }
   ```
   ✅ Expected: 200 OK with access_token

5. **Test 4: Login with Truncated Long Password**
   - Use the long password from Test 2
   ✅ Expected: 200 OK (truncation ensures consistency)

6. **Test 5: Duplicate Email**
   ```json
   POST /api/register
   {
     "name": "Another User",
     "email": "test@example.com",
     "password": "AnotherPass456",
     "role": "employer"
   }
   ```
   ✅ Expected: 400 Bad Request with `"Email already registered"`

7. **Test 6: Invalid Password (Too Short)**
   ```json
   POST /api/register
   {
     "name": "Bad Pass",
     "email": "badpass@example.com",
     "password": "123",
     "role": "jobseeker"
   }
   ```
   ✅ Expected: 422 Unprocessable Entity (Pydantic validation)

8. **Verify MongoDB**
   - Check MongoDB Atlas
   - Confirm user document created with hashed password
   - Confirm `created_at` field populated

### Phase 3: Production Deployment

#### Option A: Railway (Recommended - Your Current Setup)

1. **Push Changes to Git**
   ```bash
   git add requirements.txt auth.py models.py main.py
   git commit -m "fix: handle bcrypt 72-byte limit and fix password hashing compatibility"
   git push origin main  # or your default branch
   ```

2. **Redeploy on Railway**
   - Go to Railway.app dashboard
   - Select your project "jhv-backend"
   - Click "Deploy" or wait for auto-deployment on git push
   - Monitor deployment logs:
     ```
     ✅ Dependencies installing...
     ✅ Building...
     ✅ Starting application...
     ```

3. **Verify Production Deployment**
   ```bash
   curl -X GET https://jhv-backend-production.up.railway.app/docs
   # Should return FastAPI Swagger UI
   ```

#### Option B: Environment Variables - Verify Railway Settings

Navigate to Railway project settings and verify:

- [ ] `MONGO_URL`: Points to MongoDB Atlas (verify connection string format)
- [ ] `SECRET_KEY`: Set and non-empty
- [ ] `ALGORITHM`: Set (typically "HS256")
- [ ] `RAPIDAPI_KEY`: Set (if using job search features)

**Do NOT expose these in code - verify they're in Railway environment!**

### Phase 4: Frontend Validation

**File**: Frontend registration component (React Vite)

1. **Verify API Endpoint**
   ```javascript
   // Check that frontend points to production backend
   const API_URL = "https://jhv-backend-production.up.railway.app";
   
   // NOT: http://localhost:8000 or wrong domain
   ```

2. **Check Request Headers**
   ```javascript
   headers: {
     "Content-Type": "application/json",
     // CORS credentials if needed
   }
   ```

3. **Test Registration Flow (Production)**
   - Go to www.jobhirevia.com
   - Navigate to registration page
   - Fill form with:
     - Name: "Test Frontend User"
     - Email: "frontend@example.com"
     - Password: "FrontendPass123"
     - Role: "jobseeker"
   - Click Register
   - ✅ Expected: Redirect to login or success message
   - ❌ If error: Check browser console (F12 → Network → /api/register)

4. **Test Login Flow (Production)**
   - Use credentials from registration
   - ✅ Expected: JWT token received, redirect to dashboard

### Phase 5: Comprehensive System Testing

#### Test Case 1: Complete Registration → Login Flow
```
1. Register new user (frontend or /docs)
2. Verify user in MongoDB Atlas
3. Login with same credentials
4. Verify JWT token received
5. Access protected endpoint with token
```

#### Test Case 2: Password Edge Cases
```
1. Register with maximum length password (128 chars)
2. Register with characters that need UTF-8 encoding (émojis, special chars)
3. Verify login works with same password
```

#### Test Case 3: Concurrent Requests
```
1. Rapid registrations from multiple users
2. Verify no race conditions in MongoDB
3. Verify consistent hashing across requests
```

#### Test Case 4: Error Handling
```
1. Empty password field → 422 Validation Error
2. Invalid email format → 422 Validation Error
3. SQL injection attempt in name → Safely rejected
4. Very long payload → Request size limit
```

---

## Troubleshooting Guide

### Problem: Still Getting 500 Error on /api/register

**Step 1**: Check backend logs on Railway
```bash
# In Railway dashboard, click "Logs" tab
# Look for:
- Python version ✅ Should be 3.10+
- Package versions ✅ bcrypt==4.0.1 should appear
- Import errors ❌ If present, dependencies not installed
```

**Step 2**: Verify Dependencies Installed
```bash
# On your local machine:
pip list | grep -E "bcrypt|passlib"
# Should show:
# bcrypt 4.0.1
# passlib 1.7.4
```

**Step 3**: Check SECRET_KEY and ALGORITHM
```bash
# In your Railway environment variables, verify:
echo $SECRET_KEY  # Should return a value
echo $ALGORITHM   # Should return "HS256" or similar
# If empty, set them immediately
```

**Step 4**: Test Database Connection
```python
# Run this in Railway console or local environment:
from database import users_collection
result = users_collection.find_one()
print("Connection OK" if result or result is None else "Connection FAILED")
```

### Problem: Login Fails After Registration

**Cause**: Hashing inconsistency (password truncation not applied on login)

**Solution**: 
- ✅ Already fixed in updated auth.py
- Verify both registration and login use `_truncate_password()` (they do)
- Clear old hashed passwords from database and re-register

### Problem: CORS Error on Frontend

**Error Message**: `Access to XMLHttpRequest from origin 'https://www.jobhirevia.com' blocked by CORS`

**Step 1**: Verify domain in allow_origins
```python
# main.py lines 77-85
allow_origins=[
    "https://jobhirevia.com",      # ✅ Without www
    "https://www.jobhirevia.com"   # ✅ With www
]
```

**Step 2**: Check frontend URL matches exactly
```javascript
// Frontend code must use exact domain:
fetch("https://jhv-backend-production.up.railway.app/api/register")
// NOT: fetch("http://jhv-backend-production.up.railway.app/...")
// NOT: fetch("../api/register")
```

**Step 3**: Verify credentials header if needed
```javascript
fetch(..., {
  method: "POST",
  credentials: "include",  // If using cookies
  headers: { "Content-Type": "application/json" }
})
```

### Problem: "ValueError: password cannot be longer than 72 bytes"

**This should NOT happen now**, but if it does:

**Cause**: Truncation function not being called

**Check**:
1. Did you save auth.py changes? ✅
2. Did you redeploy? ✅
3. Did you rebuild on Railway? ✅

**Verify**:
```bash
# Local test:
python -c "from auth import _truncate_password; pwd = 'x'*100; print(len(_truncate_password(pwd).encode('utf-8')))"
# Should output: 72
```

---

## Files Changed Summary

| File | Changes | Impact |
|------|---------|--------|
| `requirements.txt` | Added `bcrypt==4.0.1` | Fixes compatibility |
| `auth.py` | Added password truncation logic | Fixes 72-byte error + consistency |
| `models.py` | Added `Field()` constraints on passwords | Early validation, better errors |
| `main.py` | Added `Field` import + password constraints in models | Better request validation |
| CORS config | ✅ No changes (already correct) | Already working |

---

## Expected Results After Deployment

✅ **Before**: 
- POST /api/register → 500 Internal Server Error
- Logs: `AttributeError: module 'bcrypt' has no attribute 'about'` + `ValueError: password cannot be longer than 72 bytes`

✅ **After**:
- POST /api/register with valid data → 201 Created
- User created in MongoDB with hashed password
- Login with same password → 200 OK with token
- Long passwords handled safely
- Invalid passwords → 422 Unprocessable Entity (from Pydantic)

---

## Next Steps

1. **Commit and push** these changes to Git
2. **Redeploy** on Railway (auto-deploy or manual)
3. **Monitor logs** during deployment
4. **Test /api/register** via FastAPI /docs endpoint
5. **Verify** user created in MongoDB Atlas
6. **Test frontend** registration flow
7. **Monitor production** logs for any new errors

---

## Support Contacts

- **Backend Logs**: Railway Dashboard → Logs tab
- **Database**: MongoDB Atlas → Browse Collections
- **Frontend Logs**: Browser DevTools (F12) → Network & Console
- **Environment Variables**: Railway Project Settings → Environment Variables

---

**Deployment Status**: Ready for immediate release ✅
