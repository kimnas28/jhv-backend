# Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- GitHub repository connected to Railway
- MongoDB Atlas cluster (for production)

## Environment Variables

Set the following environment variables in Railway:

```
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/JobSystem?retryWrites=true&w=majority
RAPIDAPI_KEY=your_rapidapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Deployment Steps

1. **Connect Repository to Railway**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub"
   - Choose this repository

2. **Configure Environment Variables**
   - In Railway dashboard, go to Variables
   - Add all environment variables from `.env.example`
   - Use your actual API keys and MongoDB Atlas connection string

3. **Railway Automatically Detects Configuration**
   - `Procfile` - Specifies how to start the app
   - `railway.json` - Optional deployment configuration
   - `runtime.txt` - Specifies Python 3.13.13
   - `requirements.txt` - Python dependencies

4. **Deployment**
   - Push to GitHub (Railway watches the repository)
   - Railway will automatically:
     - Install dependencies from `requirements.txt`
     - Build the application
     - Start the app using the `Procfile`

## Important Notes

### Python 3.13 Compatibility
- All dependencies are updated to support Python 3.13
- `pydantic-core==2.14.1` requires pre-built wheels (which are available for Python 3.13)
- `python-multipart` is included for form data handling

### Database Connection
- MongoDB Atlas is recommended for production
- Make sure your MongoDB connection string in `MONGO_URL` includes:
  - `retryWrites=true`
  - `w=majority`
- The app will fail with a clear error if `MONGO_URL` is not set

### File Uploads
- The `/api/analyze-resume` endpoint accepts PDF and DOCX files
- Maximum file size handled by uvicorn default (100MB)
- `python-multipart` is required for file uploads

### First Deployment
- Check Railway logs if deployment fails
- Verify all environment variables are set correctly
- Ensure MongoDB Atlas IP whitelist allows Railway's outbound IPs

## Monitoring

- Monitor logs in Railway dashboard
- Check application health at `/` endpoint (FastAPI docs)
- Uvicorn runs on the port assigned by Railway (via `$PORT` environment variable)

## Troubleshooting

**"MONGO_URL environment variable is not set"**
- Add `MONGO_URL` to Railway Variables
- Restart the application

**"Connection refused" for MongoDB**
- Check MongoDB Atlas IP whitelist
- For Railway: whitelist `0.0.0.0/0` (or specific IP ranges if available)
- Verify connection string format

**"Form data requires python-multipart"**
- Already fixed in requirements.txt
- Redeploy if this error appears
