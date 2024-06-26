import boto3
from botocore.config import Config
from botocore.session import get_session
import os

from core.logger import logging
from core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

config = Config(
    region_name=settings.AWS_REGION,
    signature_version="v4",
)


def create_aws_session():
    try:
        print(f"AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID}")
        print(f"AWS_SECRET_ACCESS_KEY: {settings.AWS_SECRET_ACCESS_KEY}")
        print(f"AWS_PROFILE: {settings.AWS_PROFILE}")
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            svc = boto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        elif settings.AWS_PROFILE:
            svc = boto3.Session(
                profile_name=settings.AWS_PROFILE,
            )
        else:
            svc = boto3.Session(config=config)

        logger.error(f"Created AWS session: {svc}")
    except Exception as e:
        logger.error(f"Error creating AWS session: {e}")
        session = get_session()
        sts_client = session.create_client("sts")

        assumedRoleObject = sts_client.assume_role(
            RoleArn=f"{os.environ['AWS_ROLE_ARN']}",
            RoleSessionName="Test1",
        )
        svc = boto3.Session(
            aws_access_key_id=assumedRoleObject["Credentials"]["AccessKeyId"],
            aws_secret_access_key=assumedRoleObject["Credentials"]["SecretAccessKey"],
            aws_session_token=assumedRoleObject["Credentials"]["SessionToken"],
        )

    return svc


def create_aws_service_client(service_name: str):
    return create_aws_session().client(service_name, config=config)


def create_bucket(bucket_name: str, region=None):
    try:
        if region is None:
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region})
    except Exception as e:
        logger.error(f"Error creating bucket {bucket_name}: {e}")
        return False
    return True


s3 = create_aws_service_client("s3")
