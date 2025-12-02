# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Refresh Plus is an employee accommodation booking platform with a point-based ticketing system. The system uses a fair lottery mechanism where employees submit booking requests (PENDING status), and a nightly batch job (00:00 KST) processes them, awarding accommodations to the highest-scoring users.

**Core Business Logic**: Users create bookings in PENDING status. The `daily_ticketing` batch job (backend/app/batch/daily_ticketing.py) runs nightly via Railway Cron, sorting PENDING bookings by user points and marking the highest scorer as WON, others as LOST. Points are deducted only on WON status.

## Development Commands

### Backend (FastAPI + Python)
```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run single test module
pytest tests/test_bookings.py -v

# Run all tests with coverage
pytest --cov=app

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Test batch jobs locally
python backend/batch/run_daily_ticketing.py
python backend/batch/run_score_recovery.py
```

### Frontend (Next.js + TypeScript)
```bash
# Setup
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build
npm start

# Lint
npm run lint
```

### Railway Deployment
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and initialize
railway login
railway init

# Deploy backend
cd backend
railway up

# View logs
railway logs

# Open Railway dashboard
railway open
```

## Architecture & Key Concepts

### Backend Architecture (Three-Layer)

1. **Routes Layer** (`backend/app/routes/`): API endpoints, request validation
2. **Services Layer** (`backend/app/services/`): Business logic, orchestration
3. **Models Layer** (`backend/app/models/`): SQLAlchemy ORM models

**Pattern**: Routes call Services, Services orchestrate Models + Integrations. Never skip the service layer.

### Booking State Machine

```
User creates booking → PENDING
                         ↓
Daily batch job (00:00) → WON (highest score) or LOST
                         ↓
WON bookings → COMPLETED (after checkout date)
```

**Critical**: Bookings start as PENDING. Points are NOT deducted immediately—only when batch job marks status as WON.

### Authentication Flow

- Frontend: Clerk authentication → JWT token
- Backend: `app/dependencies.py::get_current_user()` validates JWT via `app/integrations/clerk.py::verify_token()`
- All protected routes use `Depends(get_current_user)`

### Notification System

Dual-channel notifications:
- **Android**: Firebase Cloud Messaging (`app/integrations/firebase_service.py`)
- **iOS/PC**: Kakao Talk Channel API (`app/integrations/kakao_service.py`)

Services call notification integrations directly. No event queue system currently implemented.

### Frontend Data Flow

```
Component → Custom Hook (useAccommodations, useBookings, useWishlist)
                ↓
        React Query (caching)
                ↓
        API Client (lib/api.ts)
                ↓
        Backend API
```

**Pattern**: Components never call API directly. Always use custom hooks which wrap React Query for caching and state management.

### Batch Jobs (Railway Cron)

Located in `backend/app/batch/`:
- `daily_ticketing.py`: Runs at 00:00 KST (15:00 UTC), processes PENDING bookings
- `score_recovery.py`: Runs hourly, recovers user points based on POINTS_RECOVERY_HOURS

**Deployment**: Railway Cron services trigger standalone scripts:
- `backend/batch/run_daily_ticketing.py`
- `backend/batch/run_score_recovery.py`

These scripts import and execute the batch job functions. Configure cron schedules in Railway dashboard or `railway.toml`.

## Deployment Architecture

```
Railway Project
├── Service: Backend API
│   ├── Start: uvicorn app.main:app
│   └── Port: $PORT (auto-assigned)
├── Service: Daily Ticketing Cron
│   ├── Schedule: 0 15 * * * (00:00 KST)
│   └── Command: python batch/run_daily_ticketing.py
└── Service: Score Recovery Cron
    ├── Schedule: 0 * * * * (hourly)
    └── Command: python batch/run_score_recovery.py

Vercel Project
└── Frontend (Next.js)
```

### Railway Configuration Files

- `backend/railway.json`: Main API service config
- `backend/Procfile`: Process definition for Railway
- `backend/nixpacks.toml`: Build configuration
- `backend/runtime.txt`: Python version specification
- `backend/batch/railway_*.json`: Cron job configs

## File Organization Patterns

### Adding New Backend Features

1. Create model in `backend/app/models/feature.py`
2. Create schemas in `backend/app/schemas/feature.py` (Pydantic for validation)
3. Create service in `backend/app/services/feature_service.py` (business logic)
4. Create routes in `backend/app/routes/feature.py` (API endpoints)
5. Register router in `backend/app/main.py`

### Adding New Frontend Features

1. Define types in `frontend/src/types/feature.ts`
2. Create API functions in `frontend/src/lib/api.ts`
3. Create custom hook in `frontend/src/hooks/useFeature.ts`
4. Create components in `frontend/src/components/feature/`
5. Create page in `frontend/src/app/(protected)/feature/page.tsx`

### Adding New Batch Jobs

1. Create job function in `backend/app/batch/new_job.py`
2. Create standalone runner in `backend/batch/run_new_job.py`
3. Create Railway config in `backend/batch/railway_new_job.json`
4. Deploy as new Railway Cron service

## Environment Configuration

### Backend Required Variables (.env or Railway Variables)
- `DATABASE_URL`: PostgreSQL/Turso connection string
- `CLERK_SECRET_KEY`: For JWT validation
- `FIREBASE_CREDENTIALS_PATH`: For push notifications (or use FIREBASE_CREDENTIALS_BASE64)
- `KAKAO_REST_API_KEY`: For Kakao Talk integration
- `PORT`: Auto-assigned by Railway (use $PORT in commands)
- `ENVIRONMENT`: production/development
- `CORS_ORIGINS`: JSON array of allowed frontend origins

### Frontend Required Variables (.env.local or Vercel Environment)
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Public Clerk key
- `NEXT_PUBLIC_API_URL`: Backend API URL (Railway URL)
- `NEXT_PUBLIC_FIREBASE_*`: Firebase configuration for FCM

**Note**: Variables prefixed with `NEXT_PUBLIC_` are exposed to browser.

### Railway-Specific Environment Setup

Railway automatically injects `PORT` variable. Always use `$PORT` in start commands:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For cron jobs, copy all environment variables from main service to ensure database connectivity and API access.

## Database Schema Notes

- **Users**: `current_points` tracks available points, `last_point_recovery` for recovery timing
- **Bookings**: `winning_score_at_time` stores user's score when booking was created (for batch job sorting)
- **Accommodations**: `available_rooms` managed manually, not automatically decremented
- **Wishlist**: `notify_when_bookable` flag triggers notifications when user score >= avg winning score

## Critical Integration Points

### Clerk Authentication
Placeholder implementation in `backend/app/integrations/clerk.py::verify_token()` currently returns mock user ID. Replace with actual Clerk SDK implementation for production.

### Firebase Admin SDK
Requires Firebase credentials. Two options for Railway:
1. Base64 encode credentials and use `FIREBASE_CREDENTIALS_BASE64` env var
2. Use Railway Volumes to mount credentials file

Initialize once in `FirebaseService.__init__()`. Multiple initialization attempts will fail.

### Kakao Talk API
Uses REST API with bearer token authentication. Message format follows Kakao's template object structure.

## Testing Approach

- Backend tests use pytest with async support
- Use `AsyncClient` from httpx for API endpoint testing
- Mock external services (Firebase, Kakao) in tests
- Test batch jobs locally before deploying to Railway cron

## Common Patterns

### Async Database Queries
Always use async/await with SQLAlchemy. Example:
```python
result = await db.execute(select(Model).where(Model.field == value))
item = result.scalar_one_or_none()
```

### Error Handling in Routes
```python
from fastapi import HTTPException

if not resource:
    raise HTTPException(status_code=404, detail="Resource not found")
```

### React Query Cache Invalidation
```typescript
queryClient.invalidateQueries({ queryKey: ["resource-key"] });
```

### Railway Port Binding
Always bind to `0.0.0.0` and use Railway's `$PORT`:
```python
# ✅ Correct
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# ❌ Wrong (hardcoded port)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Deployment Workflow

### Backend to Railway
1. Commit and push code to GitHub
2. Railway auto-deploys on push (if connected)
3. Or manually: `railway up` from `backend/` directory
4. Verify deployment: `railway logs`
5. Check health: `curl https://your-app.railway.app/health`

### Batch Jobs to Railway
1. Create new service in Railway project
2. Select same GitHub repo
3. Set root directory: `backend`
4. Set service type: Cron
5. Configure schedule (crontab syntax)
6. Set command: `python batch/run_*.py`
7. Copy environment variables from main service

### Frontend to Vercel
1. Connect GitHub repo to Vercel
2. Select `frontend` as root directory
3. Set environment variables in Vercel dashboard
4. Vercel auto-deploys on push to main branch
5. Preview deployments on PR creation

## API Documentation

Interactive API docs available at `https://your-app.railway.app/docs` in production (FastAPI auto-generates Swagger UI).

Local development: `http://localhost:8000/docs`

## Troubleshooting

### Railway Build Failures
- Check `railway logs --deployment`
- Verify `requirements.txt` has all dependencies
- Ensure `runtime.txt` specifies correct Python version

### Cron Jobs Not Running
- Verify cron schedule syntax (use crontab.guru)
- Check environment variables are set on cron service
- View logs: `railway logs --service <cron-service-name>`

### Database Connection Issues
- Ensure `DATABASE_URL` uses correct async driver:
  - PostgreSQL: `postgresql+asyncpg://...`
  - Turso: `libsql://...`
- Run migrations: `railway run alembic upgrade head`

### Port Binding Errors
- Always use `$PORT` in Railway commands
- Never hardcode port 8000 in production config
- Railway assigns random port, your app must bind to it
