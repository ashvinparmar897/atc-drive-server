from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import users_router, folders_router, files_router
from app.core.config import settings
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(folders_router)
app.include_router(files_router)

# Mount static files for local uploads
if settings.STORAGE_BACKEND == "local":
    os.makedirs(settings.LOCAL_UPLOADS_PATH, exist_ok=True)
    app.mount("/files/local", StaticFiles(directory=settings.LOCAL_UPLOADS_PATH), name="local_files")

@app.get("/")
def root():
    return {"msg": "ATC Drive Backend Running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database_url": settings.DATABASE_URL} 