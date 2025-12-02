# Railway Deployment Guide

This guide covers deploying Refresh Plus backend and batch jobs to Railway.

## Prerequisites

1. Railway account (https://railway.app)
2. Railway CLI installed: `npm i -g @railway/cli`
3. GitHub repository connected

## Deployment Architecture

```
Railway Project: refresh-plus
├── Service 1: Backend API (main server)
├── Service 2: Daily Ticketing (cron job)
├── Service 3: Score Recovery (cron job)
└── Database: PostgreSQL/Turso
```

## Step 1: Deploy Backend API

### Via Railway Dashboard

1. Create new project on Railway
2. Click "New Service" → "GitHub Repo"
3. Select your repository
4. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Via Railway CLI

```bash
cd backend
railway login
railway init
railway up
```

### Set Environment Variables

In Railway Dashboard → Variables, add:

```env
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=sk_...
CLERK_PUBLISHABLE_KEY=pk_...
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id
KAKAO_REST_API_KEY=your_key
KAKAO_CHANNEL_ID=your_channel
AWS_REGION=ap-northeast-2
ENVIRONMENT=production
DEBUG=False
CORS_ORIGINS=["https://your-frontend.vercel.app"]
PORT=8000
```

### Upload Firebase Credentials

Since Railway doesn't support file uploads directly:

**Option 1: Base64 Encode**
```bash
# Encode your firebase-credentials.json
cat firebase-credentials.json | base64

# Add as environment variable
FIREBASE_CREDENTIALS_BASE64=<encoded_string>
```

Then update `backend/app/integrations/firebase_service.py`:
```python
import os
import base64
import json

# In _initialize method:
if settings.FIREBASE_CREDENTIALS_BASE64:
    cred_json = json.loads(base64.b64decode(settings.FIREBASE_CREDENTIALS_BASE64))
    cred = credentials.Certificate(cred_json)
```

**Option 2: Use Railway Volumes**
1. Create a volume in Railway
2. Mount to `/app/credentials`
3. Set `FIREBASE_CREDENTIALS_PATH=/app/credentials/firebase-credentials.json`

## Step 2: Deploy Batch Jobs as Cron Services

Railway supports cron jobs via their Cron service type.

### Daily Ticketing Job (00:00 KST)

1. Create new service in Railway project
2. Select same GitHub repo
3. Configure:
   - **Service Name**: `daily-ticketing-cron`
   - **Root Directory**: `backend`
   - **Service Type**: Cron
   - **Cron Schedule**: `0 15 * * *` (00:00 KST = 15:00 UTC)
   - **Command**: `python batch/run_daily_ticketing.py`

Or via `railway.toml`:
```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python batch/run_daily_ticketing.py"
cronSchedule = "0 15 * * *"
restartPolicyType = "NEVER"
```

### Score Recovery Job (Every Hour)

1. Create new service in Railway project
2. Select same GitHub repo
3. Configure:
   - **Service Name**: `score-recovery-cron`
   - **Root Directory**: `backend`
   - **Service Type**: Cron
   - **Cron Schedule**: `0 * * * *` (every hour)
   - **Command**: `python batch/run_score_recovery.py`

### Share Environment Variables

Copy all environment variables from the main backend service to the cron services (Railway allows copying variables between services).

## Step 3: Database Setup

### Option 1: Railway PostgreSQL

1. In Railway project, click "New" → "Database" → "PostgreSQL"
2. Railway auto-generates `DATABASE_URL`
3. Update backend `DATABASE_URL` to use PostgreSQL:
   ```
   postgresql+asyncpg://user:pass@host:port/dbname
   ```

### Option 2: Turso (SQLite Edge)

1. Sign up at https://turso.tech
2. Create database
3. Get connection URL
4. Add to Railway variables:
   ```
   DATABASE_URL=libsql://your-db.turso.io?authToken=your-token
   ```

### Run Migrations

After first deployment:
```bash
# Via Railway CLI
railway run alembic upgrade head

# Or add to build command
buildCommand = "pip install -r requirements.txt && alembic upgrade head"
```

## Step 4: Frontend Deployment (Vercel)

Frontend deploys to Vercel (recommended for Next.js):

```bash
cd frontend
npm install -g vercel
vercel login
vercel
```

Set environment variables in Vercel dashboard:
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
# ... other Firebase config
```

## Monitoring & Logs

### View Logs
```bash
# Backend API logs
railway logs

# Specific service logs
railway logs --service daily-ticketing-cron
railway logs --service score-recovery-cron
```

### Health Checks

Railway automatically monitors your services. Add custom health check:

```python
# backend/app/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now().isoformat()
    }
```

Configure in Railway:
- **Health Check Path**: `/health`
- **Health Check Timeout**: 30s

## Cost Optimization

Railway pricing tips:
- Hobby plan: $5/month (includes $5 credit)
- Each service uses resources independently
- Consider combining cron jobs into single service with internal scheduling if cost is concern

### Alternative: Single Service with APScheduler

If Railway cron pricing is too high, run all jobs in main service:

```python
# backend/app/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.batch.daily_ticketing import process_daily_ticketing
from app.batch.score_recovery import process_score_recovery

scheduler = AsyncIOScheduler()

# Daily ticketing at 00:00 KST
scheduler.add_job(
    process_daily_ticketing,
    'cron',
    hour=0,
    minute=0,
    timezone='Asia/Seoul'
)

# Score recovery every hour
scheduler.add_job(
    process_score_recovery,
    'cron',
    minute=0
)

# Start in main.py lifespan
```

Add to requirements.txt:
```
APScheduler==3.10.4
```

## Troubleshooting

### Build Failures

Check Railway build logs:
```bash
railway logs --deployment
```

Common issues:
- Missing dependencies in requirements.txt
- Python version mismatch (ensure `runtime.txt` has `python-3.11`)

### Database Connection Issues

Verify `DATABASE_URL` format:
```python
# For PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# For Turso
DATABASE_URL=libsql://db.turso.io?authToken=token
```

### Cron Jobs Not Running

- Check cron schedule syntax (use crontab.guru)
- Verify environment variables are copied to cron services
- Check logs for the specific cron service

### Firebase Initialization Errors

Ensure credentials are properly loaded:
```python
# Add logging
logger.info(f"Firebase credentials path: {settings.FIREBASE_CREDENTIALS_PATH}")
logger.info(f"Path exists: {os.path.exists(settings.FIREBASE_CREDENTIALS_PATH)}")
```

## Production Checklist

- [ ] Backend deployed and accessible
- [ ] Database connected and migrated
- [ ] All environment variables set
- [ ] Firebase credentials uploaded
- [ ] Daily ticketing cron configured (00:00 KST)
- [ ] Score recovery cron configured (hourly)
- [ ] Frontend connected to backend API
- [ ] CORS origins configured correctly
- [ ] Health checks passing
- [ ] Sentry configured for error tracking
- [ ] Logs being captured

## Useful Commands

```bash
# Deploy from CLI
railway up

# View all services
railway status

# Open Railway dashboard
railway open

# Run command in Railway environment
railway run python manage.py shell

# Link local project to Railway
railway link

# Get environment variables
railway variables
```

## Support

For Railway-specific issues:
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app
