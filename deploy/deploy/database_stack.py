# secretsmanagerfrom os import path, environ
import json
from aws_cdk import Stack
from constructs import Construct

from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager
)
from aws_cdk import CfnOutput, Duration, RemovalPolicy
from .utils import get_from_config_environ_or_default

class DatabaseStack(Construct):
    db: rds.DatabaseInstance

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

        # TODO: add roles

        secret_db_creds = secretsmanager.Secret(
            self,
            "DBCreds",
            secret_name=f"/{namespace}/database/creds",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({"username": dbUser}),
                exclude_punctuation=True,
                generate_string_key="password",
            ),
        )

        subnet_group = rds.SubnetGroup(self, "MySubnetGroup",
            description="description",
            vpc=vpc,
            removal_policy=RemovalPolicy.DESTROY,
            subnet_group_name="subnetGroupName",
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            )
        )

        db = rds.DatabaseInstance(
            self,
            "moodme-postgres",
            instance_identifier="moodme-backend",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_14
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.M6G, 
                ec2.InstanceSize.LARGE
            ),
            allocated_storage=200,
            max_allocated_storage=500,
            credentials=rds.Credentials.from_secret(secret_db_creds),
            database_name=database_name,
            vpc=vpc,
            enable_performance_insights=True,
            performance_insight_retention=rds.PerformanceInsightRetention.DEFAULT,
            monitoring_interval=Duration.seconds(60),
            publicly_accessible=False,
            subnet_group=subnet_group,
            backup_retention=Duration.days(7),
        )

        # rds_proxy = db.add_proxy(
        #     "rds-proxy",
        #     vpc=vpc,
        #     secrets=[secret_db_creds],
        #     vpc_subnets=ec2.SubnetSelection(
        #         subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        #     ),
        #     debug_logging=True,
        # )

        db.connections.allow_from_any_ipv4(ec2.Port.tcp(5432), "Allow from VPC")

        CfnOutput(self, "DB Cluster Endpoint", value=db.db_instance_endpoint_address)
        self.db = db

    def get_db(self):
        return self.db