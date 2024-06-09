import boto3
from botocore.exceptions import ClientError
from typing import List
from controllers.aws import s3

from .schemas import ShowBucket


class StorageController:
    s3_client: boto3.client = s3

    async def list_buckets(self) -> List[ShowBucket]:
        try:
            resp = self.s3_client.list_buckets()
            buckets = resp["Buckets"]
            return [ShowBucket(name=bucket["Name"]) for bucket in buckets]
        except ClientError as e:
            print(e)
            return []
