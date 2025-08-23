# ATC Drive Backend (FastAPI)

## Features
- User authentication (JWT, password reset)
- Folder/file management with S3 storage
- Role-based access control (Admin, Editor, Viewer)
- Async multi-file upload (100 files, 100MB each)
- PostgreSQL database

## Setup
1. Create a PostgreSQL database and update `app/database.py` with your credentials.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set AWS credentials for S3 in environment variables or `app/s3_utils.py`.
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Folder Structure
- `app/` - Main FastAPI app
- `app/models.py` - SQLAlchemy models
- `app/schemas.py` - Pydantic schemas
- `app/routers/` - API endpoints
- `app/s3_utils.py` - S3 upload/download helpers

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`

--- 