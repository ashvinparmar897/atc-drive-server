import boto3
import os
from botocore.exceptions import NoCredentialsError
from fastapi import UploadFile
from uuid import uuid4

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

async def upload_file_to_s3(file: UploadFile, folder: str = ""):
    ext = file.filename.split(".")[-1]
    key = f"{folder}/{uuid4()}.{ext}"
    content = await file.read()
    try:
        s3.put_object(Bucket=AWS_S3_BUCKET, Key=key, Body=content)
        return key
    except NoCredentialsError:
        raise Exception("AWS credentials not found")


def get_s3_download_url(key: str, expires_in=3600):
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': AWS_S3_BUCKET, 'Key': key},
        ExpiresIn=expires_in
    )
    return url 