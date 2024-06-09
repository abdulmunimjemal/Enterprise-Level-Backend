import boto3
from botocore.config import Config

from core.config import get_settings

settings = get_settings()

config = Config(
    region_name=settings.AWS_REGION,
    signature_version="v4",
)


def create_aws_session():
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

    return svc


def create_aws_service_client(service_name: str):
    return create_aws_session().client(service_name, config=config)


s3 = create_aws_service_client("s3")
