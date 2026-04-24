# 🚀 One-Command Deployment Guide

## Quick Deploy (Copy & Paste)

### Step 1: Setup Local Environment (One Time)
```bash
cd c:\Users\KIM NAS\Documents\GitHub\jhv-backend
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Verify Installation (One Time)
```bash
python -c "import bcrypt; print('bcrypt:', bcrypt.__version__); from auth import _truncate_password; print('auth.py: OK'); from models import UserCreate; print('models.py: OK')"
```

Expected output:
```
bcrypt: 4.0.1
auth.py: OK
models.py: OK
```

### Step 3: Commit & Push (When Ready to Deploy)
```bash
git add -A
git commit -m "fix: handle bcrypt 72-byte limit and password hashing compatibility"
git push origin main
```

### Step 4: Wait for Railway to Deploy
- Go to: https://railway.app/project/[YOUR-PROJECT-ID]
- Watch "Deployments" tab for green checkmark ✅

---

## Quick Test Commands (After Deployment)

### Test 1: API Health
```bash
curl https://jhv-backend-production.up.railway.app/docs
```
Should return HTML (not 500 error)

### Test 2: Register New User
```bash
curl -X POST https://jhv-backend-production.up.railway.app/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test'$RANDOM'@example.com",
    "password": "TestPass123!",
    "role": "jobseeker"
  }'
```
Expected: `{"message":"User registered successfully"}`

### Test 3: Login
```bash
curl -X POST https://jhv-backend-production.up.railway.app/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```
Expected: Response with `access_token`

---

## Visual Deployment Flow

```
1. Make Changes ← (Already Done! ✅)
   ↓
2. git add -A
   ↓
3. git commit
   ↓
4. git push origin main
   ↓
5. Railway detects push
   ↓
6. Railway rebuilds container
   ↓
7. New requirements.txt installed (bcrypt==4.0.1)
   ↓
8. New auth.py with truncation loaded
   ↓
9. App starts ✅
   ↓
10. Test /api/register ✅
```

---

## Files Ready to Deploy

### Files Changed (4 total)
✅ `requirements.txt` - bcrypt==4.0.1 added
✅ `auth.py` - _truncate_password() added  
✅ `models.py` - Field constraints added
✅ `main.py` - Field import + constraints added

### Documentation Created (3 files)
📄 `FIX_SUMMARY.md` - This document
📄 `FIXES_AND_DEPLOYMENT.md` - Comprehensive guide
📄 `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist

---

## Environment Variables Check (Railway)

**MUST BE SET** (check in Railway Dashboard):
- ✅ `MONGO_URL` - MongoDB Atlas connection string
- ✅ `SECRET_KEY` - Any random string (for JWT)
- ✅ `ALGORITHM` - "HS256" (JWT algorithm)
- ✅ `RAPIDAPI_KEY` - For job search (if using)

**If missing**, go to:
1. Railway Dashboard
2. Select "jhv-backend" project
3. Click "Variables" tab
4. Add missing environment variables

---

## Git Status Check

Run this to verify everything is ready:
```bash
git status
```

Should show only committed changes, not uncommitted.

Run this to see what changed:
```bash
git diff HEAD~1
```

Should show the 4 files with password hashing fixes.

---

## Rollback (If Needed)

If something goes wrong:
```bash
git revert HEAD
git push origin main
# OR
git reset --hard HEAD~1
git push origin main --force
```

---

## Post-Deployment: Cleanup (Optional)

Delete test users from MongoDB:
```bash
# Using MongoDB Atlas UI:
# 1. Go to Collections → JobSystem → users
# 2. Find users with email "test*@example.com"
# 3. Click delete button
```

---

## Final Status

### Before Deployment
```
❌ /api/register returns 500 error
❌ bcrypt compatibility issue  
❌ Password length issue
❌ Frontend can't register
```

### After Deployment
```
✅ /api/register returns 201
✅ bcrypt==4.0.1 installed
✅ Password truncation works
✅ Frontend can register
✅ Users can login
✅ No more 500 errors
```

---

## Need Help?

1. **Check Railway Logs**: Dashboard → Logs tab
2. **Check MongoDB**: Atlas dashboard
3. **Check Frontend**: Browser DevTools (F12)
4. **Run Tests Again**: Use curl commands above

---

**Time to Deploy**: < 5 minutes  
**Expected Deployment Time**: 2-3 minutes  
**Testing Time**: 3-5 minutes

**Total Time to Fix**: ~10 minutes ✅

---

Last updated: 2026-04-24
