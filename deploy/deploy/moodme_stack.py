from os import path, environ
import yaml
from aws_cdk import Stack
from constructs import Construct

from aws_cdk import (
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_certificatemanager as acm,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_rds as rds,
    aws_lambda as awslambda,
    aws_elasticloadbalancingv2 as elb,
    aws_secretsmanager as secrets_manager,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
)
from aws_cdk import CfnOutput, Duration
from .app import __version__
from .pipeline_stack import PipelineStack
from .database_stack import DatabaseStack
from .ecr_stack import EcrStack
from .utils import get_from_config_environ_or_default


class MoodMeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        deploymentEnvironment = get_from_config_environ_or_default("deploymentEnvironment", "prod", **kwargs)
        # Cluster capacity
        min_capacity = get_from_config_environ_or_default("minCapacity", 1, **kwargs)
        max_capacity = get_from_config_environ_or_default("maxCapacity", 1, **kwargs)

        namespace = get_from_config_environ_or_default("namespace", "moodme", **kwargs)
        hostedZoneName = get_from_config_environ_or_default("hostedZoneName", f"backend.mood-me.com", **kwargs)
        domainName = get_from_config_environ_or_default("domainName", "backend.mood-me.com", **kwargs)
        hostedZoneId = get_from_config_environ_or_default("hostedZoneId", "Z08998253M9SK1N1JI6OB", **kwargs)

        hostedZoneName = f"{domainName}" if deploymentEnvironment == "prod" else f"{deploymentEnvironment}.{domainName}"
        applicationPort = get_from_config_environ_or_default("applicationPort", 80, **kwargs)
        certificateARN = get_from_config_environ_or_default("certificateARN", "", **kwargs)

        aws_secret = secrets_manager.Secret.from_secret_name_v2(self, "AccessSecret", secret_name="/moodme/aws/keys")
        db_secrets = secrets_manager.Secret.from_secret_name_v2(
            self, "DBSecretID", secret_name="/moodme/database/creds"
        )

        dbUser = ecs.Secret.from_secrets_manager(db_secrets, "username")
        dbPassword = ecs.Secret.from_secrets_manager(db_secrets, "password")
        dbDatabase = ecs.Secret.from_secrets_manager(db_secrets, "dbname")
        dbHost = ecs.Secret.from_secrets_manager(db_secrets, "host")
        dbPort = ecs.Secret.from_secrets_manager(db_secrets, "port")

        aws_access_key_id = ecs.Secret.from_secrets_manager(aws_secret, "AWS_ACCESS_KEY_ID")
        aws_secret_access_key = ecs.Secret.from_secrets_manager(aws_secret, "AWS_SECRET_ACCESS_KEY")
        aws_region = ecs.Secret.from_secrets_manager(aws_secret, "AWS_REGION")

        # Get VPC
        # vpcId = ssm.StringParameter.value_from_lookup(self, f"/{namespace}/vpc/id")
        # vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name="moodme-vpc")
        vpc = ec2.Vpc(
            self,
            "MoodMeVPC",
            max_azs=2,
            # cidr="10.5.0.0/16",
            subnet_configuration=[
                ec2.SubnetConfiguration(subnet_type=ec2.SubnetType.PUBLIC, name="Public", cidr_mask=26),
                ec2.SubnetConfiguration(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, name="Private", cidr_mask=26),
            ],
            nat_gateways=3,
        )

        hostedZone = route53.HostedZone.from_hosted_zone_attributes(
            self, "HostedZone", hosted_zone_id=hostedZoneId, zone_name=hostedZoneName
        )

        # vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=vpc_id=)
        # cert = acm.Certificate(self, "Certificate",
        #     domain_name=domainName,
        # )
        cert = acm.Certificate.from_certificate_arn(self, "Certificate", certificate_arn=certificateARN)
        cert.metric_days_to_expiry().create_alarm(self, "CertificateExpiryAlarm", threshold=30, evaluation_periods=1)

        alb = elb.ApplicationLoadBalancer(
            self,
            "ALB",
            vpc=vpc,
            internet_facing=True,
        )

        albSecurityGroup = ec2.SecurityGroup(self, "ALBSecurityGroup", vpc=vpc, allow_all_outbound=True)
        albSecurityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS traffic")
        albSecurityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP traffic")

        alb.connections.add_security_group(albSecurityGroup)
        alb.add_redirect(
            source_port=80,
            source_protocol=elb.ApplicationProtocol.HTTP,
            target_port=443,
            target_protocol=elb.ApplicationProtocol.HTTPS,
        )

        cluster = ecs.Cluster(self, "MM-Cluster", cluster_name=f"{namespace}-cluster", vpc=vpc)

        model_bucket = s3.Bucket(
            self,
            "ModelBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
        )

        dbStack = DatabaseStack(self, "DatabaseStack", vpc=vpc, **kwargs)
        db = dbStack.get_db()

        ecrStack = EcrStack(self, "EcrStack", vpc=vpc, **kwargs)
        repo = ecrStack.get_repo()

        environment = dict(
            # "DATABASE_URL": ssm.StringParameter.value_from_lookup(self, f"/{namespace}/database/url"),
            # "SECRET_KEY": ssm.StringParameter.value_from_lookup(self, f"/{namespace}/secret/key"),
            AWS_MODEL_BUCKET=model_bucket.bucket_name,
            # POSTGRES_ASYNC_URI=f"postgresql+asyncpg://{dbUser}:{dbPassword}@{dbHost}:{dbPort}/{dbDatabase}",
        )
        secrets = {
            "POSTGRES_PASSWORD": dbPassword,
            "POSTGRES_DB": dbDatabase,
            "POSTGRES_SERVER": dbHost,
            "POSTGRES_PORT": dbPort,
            "POSTGRES_USER": dbUser,
            "AWS_ACCESS_KEY_ID": aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": aws_secret_access_key,
            "AWS_REGION": aws_region,
        }

        # Create a migration
        migrationLambdaCode = awslambda.Code.from_ecr_image(repository=repo, cmd=["main.handler"])
        migration_lambda = awslambda.Function(
            self,
            "MigrationLambda",
            vpc=vpc,
            code=migrationLambdaCode,
            handler=awslambda.Handler.FROM_IMAGE,
            runtime=awslambda.Runtime.FROM_IMAGE,
            timeout=Duration.seconds(600),
            tracing=awslambda.Tracing.ACTIVE,
            environment=environment,
        )
        migration_lambda.connections.allow_to(
            db,
            ec2.Port.tcp(5432),
            "Allow from RDS",
        )

        taskRole = iam.Role(
            self,
            "ECS-TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            role_name=f"{namespace}-task-role",
            description="Role for MoodMe tasks",
        )

        taskRole.attach_inline_policy(
            iam.Policy(
                self,
                "ECS-TaskPolicy",
                statements=[
                    iam.PolicyStatement(effect=iam.Effect.ALLOW, actions=["sts:AssumeRole"], resources=["*"]),
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                        resources=[f"arn:aws:s3:::{model_bucket.bucket_name}/*"],
                    ),
                ],
            )
        )

        taskDef = ecs.TaskDefinition(
            self,
            "TaskDefinition",
            family=f"{namespace}-task",
            compatibility=ecs.Compatibility.EC2_AND_FARGATE,
            cpu="512",
            memory_mib="1024",
            network_mode=ecs.NetworkMode.AWS_VPC,
            task_role=taskRole,
        )

        container = taskDef.add_container(
            "MoodMeContainer",
            image=ecs.ContainerImage.from_ecr_repository(repository=repo),
            #   image=ecs.ContainerImage.from_asset(path.join(path.dirname(__file__), "../../")),
            memory_limit_mib=1024,
            memory_reservation_mib=512,
            environment=environment,
            secrets=secrets,
            logging=ecs.LogDriver.aws_logs(stream_prefix="moodme"),
        )

        port_mapping = ecs.PortMapping(
            container_port=applicationPort,
            protocol=ecs.Protocol.TCP,
        )

        container.add_port_mappings(port_mapping)

        ecsSG = ec2.SecurityGroup(self, "ECS-SecurityGroup", vpc=vpc, allow_all_outbound=True)
        ecsSG.connections.allow_from(albSecurityGroup, ec2.Port.tcp(applicationPort), "Allow from ALB to ECS")
        ecsSG.connections.allow_from_any_ipv4(ec2.Port.tcp(applicationPort), "Allow from VPC")
        ecsSG.connections.allow_from(
            alb, port_range=ec2.Port.tcp_range(32768, 65535), description="allow incoming traffic from ALB"
        )

        alb.connections.add_security_group(ecsSG)

        vpc.add_interface_endpoint(
            "ECR",
            service=ec2.InterfaceVpcEndpointService(f"com.amazonaws.{self.region}.ecs"),
            security_groups=[albSecurityGroup, ecsSG],
        )

        service = ecs.FargateService(
            self,
            "MoodMeService",
            cluster=cluster,
            desired_count=min_capacity,
            task_definition=taskDef,
            security_groups=[ecsSG],
            assign_public_ip=True,
        )

        targetGroupHttp = elb.ApplicationTargetGroup(
            self,
            "TargetGroupHttp",
            vpc=vpc,
            port=applicationPort,
            protocol=elb.ApplicationProtocol.HTTP,
            target_type=elb.TargetType.IP,
        )

        targetGroupHttp.configure_health_check(
            path="/health",
            protocol=elb.Protocol.HTTP,
            interval=Duration.seconds(60),
            timeout=Duration.seconds(5),
        )

        listener = alb.add_listener(
            "HttpsListener",
            open=True,
            port=443,
            certificates=[cert],
        )

        listener.add_certificates("input-cert", certificates=[cert])
        listener.add_target_groups("TargetGroups", target_groups=[targetGroupHttp])

        service.attach_to_application_target_group(targetGroupHttp)

        scalable_target = service.auto_scale_task_count(min_capacity=min_capacity, max_capacity=max_capacity)
        scalable_target.scale_on_cpu_utilization("CpuScaling", target_utilization_percent=70)
        scalable_target.scale_on_memory_utilization("MemoryScaling", target_utilization_percent=70)

        hostedZoneARecord = route53.ARecord(
            self,
            "HostedZoneARecord",
            comment="A record for the backend",
            record_name=hostedZoneName,
            zone=hostedZone,
            target=route53.RecordTarget.from_alias(route53_targets.LoadBalancerTarget(alb)),
            ttl=Duration.seconds(120),
        )

        CfnOutput(self, "Load balancer ALB DNS name", value=alb.load_balancer_dns_name)
        CfnOutput(self, "Model Bucket Name", value=model_bucket.bucket_name)

        # PipelineStack(self, "PipelineStack", **kwargs)
