# !/usr/bin/env python

import yaml
import os
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_ssm as ssm,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_codebuild as cb,
    aws_codepipeline as codepipeline,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secrets_manager,
    RemovalPolicy
)
from aws_cdk import CfnOutput, Duration
from .app import __version__


class FastAPIStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Import project config from CDK_STACK_CONFIG environment variable
        if 'CDK_STACK_CONFIG' not in os.environ:
            os.environ['CDK_STACK_CONFIG'] = 'config.yml'

        with open(os.environ['CDK_STACK_CONFIG'], 'r') as stream:
            config = yaml.safe_load(stream)

        # Cluster capacity
        min_capacity = config['MinCapacity']
        max_capacity = config['MaxCapacity']

        namespace = 'namespace' in config and config['namespace'] or 'moodme'

        # Create VPC
        vpc = ec2.Vpc(self, "MoodMeVPC", max_azs=2)

        # Create Fargate Cluster
        ecs_cluster = ecs.Cluster(
            self,
            "MoodMeECSCluster",
            vpc=vpc,
        )

        # Create Security Group to restrict access to the MoodMe service from a specific IP mask

        # MoodMe IP mask up to 65,536 possible host addresses from the MoodMe subnet
        ip_mask = '134.89.0.0/16'

        # Create a security group
        moodme_security_group = ec2.SecurityGroup(
            self, 'MoodMeSecurityGroup', vpc=vpc,
            allow_all_outbound=True
        )

        # Allow inbound access from the specified IP mask
        moodme_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(ip_mask),
            connection=ec2.Port.tcp(80)
        )

        # Create an ecr registry
        # ecr_registry = ecr.Repository(
        #     self,
        #     'MoodMeECRRegistry',
        #     repository_name='moodme-backend',
        #     image_scan_on_push=True,
        #     lifecycle_rules=[
        #         ecr.LifecycleRule(max_image_count=100)
        #     ]
        # )

        # Retrieve the AWS access key ID secret value from AWS Secrets Manager
        secret = secrets_manager.Secret.from_secret_name_v2(self, "MySecretID", secret_name="prod/s3download")

        # pipeline to build docker image
        bucket = s3.Bucket(
            self, 'MoodMeDockerImageBucket',
            bucket_name=f"{namespace}-backend-docker-image",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY
        )
        bucket_param = ssm.StringParameter(
            self, "PipelineBucketParam",
            parameter_name=f"{namespace}-backend-docker-image",
            string_value=bucket.bucket_name,
            description='cdk pipeline bucket'
        )
        ecr_repo = ecr.Repository(
            self, "ECR",
            repository_name=f"{namespace}",
            removal_policy=RemovalPolicy.DESTROY
        )
        cb_docker_build = cb.PipelineProject(
            self, f'dockerbuild',
            project_name=f"{namespace}-build",
            build_spec=cb.BuildSpec.from_source_filename(
                os.path.join(os.path.dirname(__file__), '..', "buildspec.yml"),
            ),
            environment=cb.BuildEnvironment(privileged=True),
            environment_variables={
                'ecr': cb.BuildEnvironmentVariable(value=ecr_repo.repository_uri),
                'tag': cb.BuildEnvironmentVariable(value='cdk')
            },
            description='MoodMe Docker Build Pipeline',
            timeout=Duration.minutes(60)
        )
        bucket.grant_read_write(cb_docker_build)
        ecr_repo.grant_pull_push(cb_docker_build)

        CfnOutput(
            self, "ECRURI",
            description="ECR URI",
            value=ecr_repo.repository_uri,
        )
        CfnOutput(
            self, "S3Bucket",
            description="S3 Bucket",
            value=bucket.bucket_name
        )


        docker_image = ecs.ContainerImage.from_registry(ecr_repo.repository_name)

        # Create Fargate Service and ALB
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs_patterns/ApplicationLoadBalancedTaskImageOptions.html
        image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=docker_image,
            container_port=80,
            secrets={
                "AWS_ACCESS_KEY_ID": ecs.Secret.from_secrets_manager(secret, "AWS_ACCESS_KEY_ID"),
                "AWS_SECRET_ACCESS_KEY": ecs.Secret.from_secrets_manager(secret, "AWS_SECRET_ACCESS_KEY")
            }
        )

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs_patterns/ApplicationLoadBalancedFargateService.html
        self.ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "MoodMeService",
            cluster=ecs_cluster,
            cpu=1024,
            memory_limit_mib=8192,
            desired_count=1,
            task_image_options=image_options,
            open_listener=False,
            # Since we deploy using docker
            circuit_breaker={
                'rollback': False
            }
        )

        # Get the ALB
        lb = self.ecs_service.load_balancer

        # Add the security group to the ALB
        lb.add_security_group(security_group=moodme_security_group)

        # Setup health check
        # self.ecs_service.target_group.configure_health_check(
        #     path="/health",
        #     healthy_http_codes="200-299",
        #     healthy_threshold_count=2,
        #     unhealthy_threshold_count=2,
        #     interval=Duration.seconds(300),
        #     timeout=Duration.seconds(60),
        # )

        # Increase scaling speed
        scaling = self.ecs_service.service.auto_scale_task_count(
            min_capacity=min_capacity,
            max_capacity=max_capacity,
        )

        scaling.scale_on_cpu_utilization('CpuScaling',
                                         target_utilization_percent=80,
                                         scale_in_cooldown=Duration.seconds(30),
                                         scale_out_cooldown=Duration.seconds(30),
                                         )