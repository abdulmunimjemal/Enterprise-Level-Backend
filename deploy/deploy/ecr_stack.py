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

        dbUser = get_from_config_environ_or_default('dbUser', 'moodme', **kwargs)
        namespace = get_from_config_environ_or_default('namespace', 'moodme', **kwargs)
        database_name = get_from_config_environ_or_default('database_name', 'moodme', **kwargs)
        repository_name = get_from_config_environ_or_default('repository_name', 'moodme-repo', **kwargs)

        repo = ecr.Repository(
            self,
            "repo",
            repository_name=repository_name,
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(max_image_count=10),
            ],
        )
        self.ecr = repo

        CfnOutput(self, "EcrRepository", value=repo.repository_uri)

    def get_repo(self):
        return self.ecr

