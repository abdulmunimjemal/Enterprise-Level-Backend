import boto3
from botocore.exceptions import ClientError
from typing import List
from utils.aws import s3

from core.config import get_settings
from .schemas import (
    ShowBucket,
    ModelResponse
)

settings = get_settings()
AWS_MODEL_BUCKET = settings.AWS_MODEL_BUCKET

class StorageController:
    s3_client: boto3.client = s3

    @staticmethod
    async def list_buckets() -> List[ShowBucket]:
        try:
            resp = s3.list_buckets()
            buckets = resp["Buckets"]
            return [ShowBucket(name=bucket["Name"]) for bucket in buckets]
        except ClientError as e:
            print(e)
            return []

    @staticmethod
    async def list_models() -> List[ModelResponse]:
        try:
            resp = s3.list_objects(Bucket=AWS_MODEL_BUCKET)
            print(f"resp: {resp}")
            # return [ModelResponse(name=obj["Key"]) for obj in resp["Contents"]]
            return []
        except ClientError as e:
            print(e)
            return []

