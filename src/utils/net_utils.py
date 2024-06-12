import os
import urllib.request, urllib.parse, urllib.error
import shutil
from core.common import get_settings
from .aws import s3
from fastapi import File, UploadFile
from core.logger import logger


settings = get_settings()

async def download_file(url: str, path: str):
    if "s3" in url.lower():
        await download_s3_file(url, path)
    elif "http" in url.lower():
        urllib.request.urlretrieve(url, path)
    else:
        shutil.copy(url, path)

async def download_s3_file(url: str, path: str):
    # s3.download_file(storage_bucket, url, path)
    pass

async def upload_file(file: UploadFile = File(...), bucket_name: str = settings.AWS_MODEL_BUCKET):
    # s3.upload_file(storage_bucket, url, path)
    temp_file = os.path.join("/tmp", file.filename)
    with open(temp_file, "wb") as out_file:
        out_file.write(await file.read())
    try:
        filename = f"{bucket_name}/{file.filename}"
        s3.fput_object(filename, temp_file)
    except Exception as e:
        logger.error(f"Error uploading file {file.filename}: {e}")
        return False
    return True
