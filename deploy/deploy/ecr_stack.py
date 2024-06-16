# secretsmanagerfrom os import path, environ
import json
from aws_cdk import Stack
from constructs import Construct

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_secretsmanager as secretsmanager
)
from aws_cdk import CfnOutput, Duration, RemovalPolicy
from .utils import get_from_config_environ_or_default


class EcrStack(Construct):
    ecr: ecr.Repository

    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: ec2.Vpc,
            **kwargs,
    ):
        super().__init__(scope, id)

        repo = ecr.Repository(
            self,
            "repo",
            repository_name="moodme-repo",
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(max_image_count=10),
            ],
        )
        self.ecr = repo
