import os
from typing import Optional
from io import BytesIO
import urllib.request
import urllib.parse
import urllib.error
import shutil
import tempfile
from core.config import get_settings
from .aws import s3
from fastapi import File, UploadFile
from core.logger import logging


settings = get_settings()


async def download_file(url: str, path: str):
    if "s3" in url.lower():
        await download_s3_file(url, path)
    elif "http" in url.lower():
        urllib.request.urlretrieve(url, path)
    else:
        shutil.copy(url, path)


async def download_s3_file(url: str, path: str, bucket_name: str = settings.AWS_MODEL_BUCKET):
    s3.download_file(bucket_name, url, path)


async def upload_file(file_name: str, object_name: Optional[str] = None, bucket_name: str = settings.AWS_MODEL_BUCKET):
    if object_name is None:
        object_name = os.path.basename(file_name)
    try:
        print(
            f"Uploading file {file_name} to bucket {bucket_name} as {object_name}")
        s3.upload_file(file_name, bucket_name, object_name)
    except Exception as e:
        logging.error(f"Error uploading file {file_name}: {e}")
        return False
    return True


async def upload_from_file(file: File, object_name: Optional[str] = None, bucket_name: str = settings.AWS_MODEL_BUCKET):
    if bucket_name is None:
        bucket_name = settings.AWS_MODEL_BUCKET
    buf = file.default.read()
    print("------------------")
    print(bucket_name)
    print("------------------")
    response = s3.put_object(Bucket=bucket_name, Key=object_name, Body=buf)
    print("------------------")
    return response
