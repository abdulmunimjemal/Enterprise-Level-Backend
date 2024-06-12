import urllib.request, urllib.parse, urllib.error
import shutil
import boto3
from .aws import s3

async def download_file(url: str, path: str):
    if "s3" in url.lower():
        await download_s3_file(url, path)
    elif "http" in url.lower():
        urllib.request.urlretrieve(url, path)
    else:
        shutil.copy(url, path)

async def download_s3_file(url: str, path: str):
    # s3.download_file
    pass

