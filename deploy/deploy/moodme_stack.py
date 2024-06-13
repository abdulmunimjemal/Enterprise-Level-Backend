from os import path, environ
import yaml
from aws_cdk import Stack
from constructs import Construct

from aws_cdk import (
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_certificatemanager as acm,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_route53 as route53,
    aws_elasticloadbalancingv2 as elb
)
from aws_cdk import CfnOutput, Duration
from .app import __version__
from .utils import get_from_config_environ_or_default

class MoodMeStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Cluster capacity
        min_capacity = get_from_config_environ_or_default('minCapacity', 1, **kwargs)
        max_capacity = get_from_config_environ_or_default('maxCapacity', 1, **kwargs)

        namespace = get_from_config_environ_or_default('namespace', 'moodme', **kwargs)
        hostedZoneName = get_from_config_environ_or_default('hostedZoneName', 'moodme.ai', **kwargs)
        domainName = get_from_config_environ_or_default('domainName', 'moodme.ai', **kwargs)
        applicationPort = get_from_config_environ_or_default('applicationPort', 8000, **kwargs)
        certificateARN = get_from_config_environ_or_default('certificateARN', '', **kwargs)

        # Get VPC
        # vpcId = ssm.StringParameter.value_from_lookup(self, f"/{namespace}/vpc/id")
        # vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name="moodme-vpc")
        vpc = ec2.Vpc(self, "MoodMeVPC", max_azs=2)

        # hostedZone = route53.HostedZone.from_lookup(self, "HostedZone", domain_name=hostedZoneName)

        # vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=vpc_id=)
        # cert = acm.Certificate(self, "Certificate", 
        #     domain_name=domainName,
        # )
        cert = acm.Certificate.from_certificate_arn(self, "Certificate", certificate_arn=certificateARN)
        cert.metric_days_to_expiry().create_alarm(self, "CertificateExpiryAlarm", threshold=30, evaluation_periods=1)

        alb = elb.ApplicationLoadBalancer(self, "ALB", 
            vpc=vpc, 
            internet_facing=True,
        )

        albSecurityGroup = ec2.SecurityGroup(self, "ALBSecurityGroup", vpc=vpc, allow_all_outbound=True)
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


        taskRole = iam.Role(self, "ECS-TaskRole", 
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
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
            image=ecs.ContainerImage.from_asset(path.join(path.dirname(__file__), "../../")),
            memory_limit_mib=512,
            memory_reservation_mib=256,
            environment={
                # "DATABASE_URL": ssm.StringParameter.value_from_lookup(self, f"/{namespace}/database/url"),
                # "SECRET_KEY": ssm.StringParameter.value_from_lookup(self, f"/{namespace}/secret/key"),
            },
            port_mappings=[ecs.PortMapping(container_port=applicationPort)],
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="moodme"
            )
        )

        container.add_port_mappings(ecs.PortMapping(container_port=applicationPort))

        ecsSG = ec2.SecurityGroup(self, "ECS-SecurityGroup", vpc=vpc, allow_all_outbound=True)
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
            path="/status",
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

        scalable_target = service.auto_scale_task_count(min_capacity=min_capacity, max_capacity=max_capacity)
        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70
        )
        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=70
        )

        CfnOutput(self, "Load balancer ALB DNS name", value=alb.load_balancer_dns_name)


