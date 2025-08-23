import os
from typing import List

class Settings:
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://postgres:password@127.0.0.1/atc-drive')
    AWS_ACCESS_KEY_ID: str = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY: str = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_S3_BUCKET: str = os.getenv('AWS_S3_BUCKET', '')
    AWS_REGION: str = os.getenv('AWS_REGION', 'us-east-1')
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'supersecretkey')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
    STORAGE_BACKEND: str = os.getenv('STORAGE_BACKEND', 'local')
    LOCAL_UPLOADS_PATH: str = os.getenv('LOCAL_UPLOADS_PATH', 'uploads')

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

settings = Settings()
