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
    aws_elasticloadbalancingv2 as elb,
    aws_secretsmanager as secretsmanager
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

        deploymentEnvironment = get_from_config_environ_or_default(
            'deploymentEnvironment', 'prod', **kwargs)
        # Cluster capacity
        min_capacity = get_from_config_environ_or_default(
            'minCapacity', 1, **kwargs)
        max_capacity = get_from_config_environ_or_default(
            'maxCapacity', 1, **kwargs)

        namespace = get_from_config_environ_or_default(
            'namespace', 'moodme', **kwargs)
        hostedZoneName = get_from_config_environ_or_default(
            'hostedZoneName', f'backend.mood-me.com', **kwargs)
        domainName = get_from_config_environ_or_default(
            'domainName', 'backend.mood-me.com', **kwargs)
        hostedZoneId = get_from_config_environ_or_default(
            'hostedZoneId', 'Z08998253M9SK1N1JI6OB', **kwargs)

        hostedZoneName = f'{domainName}' if deploymentEnvironment == 'prod' else f'{deploymentEnvironment}.{domainName}'
        applicationPort = get_from_config_environ_or_default(
            'applicationPort', 80, **kwargs)
        certificateARN = get_from_config_environ_or_default(
            'certificateARN', '', **kwargs)
        dbUser = get_from_config_environ_or_default(
            'dbUser', 'moodme', **kwargs)
        dbPassword = get_from_config_environ_or_default(
            'dbPassword', 'moodme', **kwargs)
        dbDatabase = get_from_config_environ_or_default(
            'dbDatabase', 'moodme', **kwargs)

        # Get VPC
        # vpcId = ssm.StringParameter.value_from_lookup(self, f"/{namespace}/vpc/id")
        # vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name="moodme-vpc")
        vpc = ec2.Vpc(self, "MoodMeVPC",
                      max_azs=2,
                      # cidr="10.5.0.0/16",
                      subnet_configuration=[
                          ec2.SubnetConfiguration(
                              subnet_type=ec2.SubnetType.PUBLIC,
                              name="Public",
                              cidr_mask=26
                          ),
                          ec2.SubnetConfiguration(
                              subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                              name="Private",
                              cidr_mask=26
                          )
                      ],
                      nat_gateways=3
                      )

        hostedZone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=hostedZoneId,
            zone_name=hostedZoneName
        )

        # vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=vpc_id=)
        # cert = acm.Certificate(self, "Certificate",
        #     domain_name=domainName,
        # )
        cert = acm.Certificate.from_certificate_arn(
            self, "Certificate", certificate_arn=certificateARN)
        cert.metric_days_to_expiry().create_alarm(
            self, "CertificateExpiryAlarm", threshold=30, evaluation_periods=1)

        alb = elb.ApplicationLoadBalancer(self, "ALB",
                                          vpc=vpc,
                                          internet_facing=True,
                                          )

        albSecurityGroup = ec2.SecurityGroup(
            self, "ALBSecurityGroup", vpc=vpc, allow_all_outbound=True)
        albSecurityGroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow HTTPS traffic"
        )

        albSecurityGroup.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow HTTPS traffic"
        )

        alb.connections.add_security_group(albSecurityGroup)

        cluster = ecs.Cluster(self, "MM-Cluster",
                              cluster_name=f"{namespace}-cluster",
                              vpc=vpc
                              )

        model_bucket = s3.Bucket(self, "ModelBucket",
                                 block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                 encryption=s3.BucketEncryption.S3_MANAGED,
                                 versioned=True,
                                 )

        dbStack = DatabaseStack(self, "DatabaseStack", vpc=vpc, **kwargs)
        db = dbStack.get_db()

        ecrStack = EcrStack(self, "EcrStack", vpc=vpc, **kwargs)
        repo = ecrStack.get_repo()

        # ecrStack = PipelineStack(self, "EcrStack", **kwargs)

        # secret_db_creds = secretsmanager.Secret(
        #     self,
        #     "DBCreds",
        #     secret_name=f"/{namespace}/database/creds",
        #     generate_secret_string={
        #         "password_length": 32,
        #         "password_characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        #     }
        # )

        # db_creds = rds.Credentials.from_generated_secret(dbUser)
        # db_cluster = rds.DatabaseCluster(self, 'MoodMeBackendRDS',
        #     engine=rds.DatabaseClusterEngine.aurora_postgres(
        #         version=rds.AuroraPostgresEngineVersion.VER_16_1,
        #     ),
        #     writer=rds.ClusterInstance.provisioned("writer",
        #         instance_type=ec2.InstanceType.of(ec2.InstanceClass.R6G, ec2.InstanceSize.XLARGE4)
        #     ),
        #     credentials=db_creds,
        #     vpc=vpc,
        # )

        taskRole = iam.Role(self, "ECS-TaskRole",
                            assumed_by=iam.ServicePrincipal(
                                "ecs-tasks.amazonaws.com"),
                            role_name=f"{namespace}-task-role",
                            description="Role for MoodMe tasks"
                            )

        taskRole.attach_inline_policy(
            iam.Policy(self, "ECS-TaskPolicy",
                       statements=[
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=["sts:AssumeRole"],
                               resources=["*"]
                           ),
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=["s3:GetObject",
                                        "s3:PutObject", "s3:DeleteObject"],
                               resources=[
                                   f"arn:aws:s3:::{model_bucket.bucket_name}/*"]
                           )
                       ]
                       )
        )

        taskDef = ecs.TaskDefinition(self, "TaskDefinition",
                                     family=f"{namespace}-task",
                                     compatibility=ecs.Compatibility.EC2_AND_FARGATE,
                                     cpu="256",
                                     memory_mib="512",
                                     network_mode=ecs.NetworkMode.AWS_VPC,
                                     task_role=taskRole
                                     )

        container = taskDef.add_container("MoodMeContainer",
                                          image=ecs.ContainerImage.from_ecr_repository(
                                              repository=repo,
                                              tag="latest"
                                          ),
                                        #   image=ecs.ContainerImage.from_asset(path.join(path.dirname(__file__), "../../")),
                                          memory_limit_mib=512,
                                          memory_reservation_mib=256,
                                          environment=dict(
                                              # "DATABASE_URL": ssm.StringParameter.value_from_lookup(self, f"/{namespace}/database/url"),
                                              # "SECRET_KEY": ssm.StringParameter.value_from_lookup(self, f"/{namespace}/secret/key"),
                                              AWS_MODEL_BUCKET=model_bucket.bucket_name,
                                              POSTGRES_USER=dbUser,
                                              POSTGRES_PASSWORD=dbPassword,
                                              POSTGRES_DB=dbDatabase,
                                              POSTGRES_SERVER=db.db_instance_endpoint_address,
                                              POSTGRES_PORT="3306",
                                              POSTGRES_URL=f"postgresql+asyncpg://{dbUser}:{dbPassword}@{db.db_instance_endpoint_address}:3306/{dbDatabase}",
                                          ),
                                          port_mappings=[ecs.PortMapping(
                                              container_port=applicationPort)],
                                          logging=ecs.LogDriver.aws_logs(
                                              stream_prefix="moodme"
                                          )
                                          )

        container.add_port_mappings(
            ecs.PortMapping(container_port=applicationPort))

        ecsSG = ec2.SecurityGroup(
            self, "ECS-SecurityGroup", vpc=vpc, allow_all_outbound=True)
        ecsSG.connections.allow_from(
            albSecurityGroup,
            ec2.Port.tcp(applicationPort),
            "Allow from ALB to ECS"
        )

        service = ecs.FargateService(self, "MoodMeService",
                                     cluster=cluster,
                                     desired_count=min_capacity,
                                     task_definition=taskDef,
                                     security_groups=[ecsSG],
                                     assign_public_ip=True,
                                     )

        targetGroupHttp = elb.ApplicationTargetGroup(
            self, "TargetGroupHttp",
            vpc=vpc,
            port=applicationPort,
            protocol=elb.ApplicationProtocol.HTTP,
            target_type=elb.TargetType.IP
        )

        targetGroupHttp.configure_health_check(
            path="/health",
            protocol=elb.Protocol.HTTP,
        )

        listener = alb.add_listener("HttpListener",
                                    open=True,
                                    port=443,
                                    )
        listener.add_certificates("input-cert", certificates=[cert])

        listener.add_target_groups("TargetGroups",
                                   target_groups=[targetGroupHttp]
                                   )

        service.attach_to_application_target_group(targetGroupHttp)

        scalable_target = service.auto_scale_task_count(
            min_capacity=min_capacity, max_capacity=max_capacity)
        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70
        )
        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=70
        )

        hostedZoneARecord = route53.ARecord(self, "HostedZoneARecord",
                                            comment="A record for the backend",
                                            record_name=hostedZoneName,
                                            zone=hostedZone,
                                            target=route53.RecordTarget.from_alias(
                                                route53_targets.LoadBalancerTarget(alb)),
                                            ttl=Duration.seconds(300)
                                            )

        CfnOutput(self, "Load balancer ALB DNS name",
                  value=alb.load_balancer_dns_name)
        CfnOutput(self, "Model Bucket Name", value=model_bucket.bucket_name)

        # PipelineStack(self, "PipelineStack", **kwargs)
