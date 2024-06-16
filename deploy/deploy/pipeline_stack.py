from typing import Optional

import aws_cdk
from aws_cdk import Stack
from aws_cdk import Stage
from aws_cdk import aws_codebuild
from aws_cdk import aws_sns as sns
from aws_cdk import pipelines
from aws_cdk import aws_secretsmanager as secretsmanager

from constructs import Construct

from .utils import clean_name, get_from_config_environ_or_default


class PipelineStack(Construct):
    def __init__(
        self,
        scope: Stack,
        id: str,
    ):
        super().__init__(scope, id)

        githubToken = secretsmanager.SecretValue.unsafe_plain_text(
            get_from_config_environ_or_default("githubTokenArn", "")
        )
        githubRepo = get_from_config_environ_or_default("githubRepo", "")
        githubUser = get_from_config_environ_or_default("githubUser", "")
        githubBranch = get_from_config_environ_or_default(
            "githubBranch", "main")

        synth = pipelines.ShellStep(
            "Synth",
            input=pipelines.GitHubSourceOptions(
                repo=[githubRepo],
                owner=githubUser,
                branch=githubBranch,
                trigger_on_push=True,
                code_build_clone_output=True,
            ),
            install_commands=[
                "npm install -g aws-cdk",
                "curl -sSL https://install.python-poetry.org/ | python3 -",
                'export PATH="$HOME/.local/bin:$PATH"',
                "poetry --version",
                "poetry install",
            ],
            commands=[
                f'''poetry run cdk synth -c account={aws_cdk.Aws.ACCOUNT_ID} -c region={aws_cdk.Aws.REGION} -c repo={githubRepo} -c branch={githubBranch} -c codestar_connection_arn={codestar_connection_arn} -a "python pipeline.py"'''
            ],
        )
        code_build_options = pipelines.CodeBuildOptions(
            build_environment=aws_codebuild.BuildEnvironment(
                build_image=aws_codebuild.LinuxBuildImage.AMAZON_LINUX_2_3
            ),
            partial_build_spec=aws_codebuild.BuildSpec.from_object(
                {"phases": {"install": {"commands": ["n 16.15.1"]}}}
            ),
        )
        self.__pipeline = pipelines.CodePipeline(
            self,
            f"pipeline-{clean_name(githubBranch)}",
            synth=synth,
            pipeline_name=f"pipeline-{clean_name(githubBranch)}",
            docker_enabled_for_synth=True,
            docker_enabled_for_self_mutation=True,
            publish_assets_in_parallel=True,
            code_build_defaults=code_build_options,
            synth_code_build_defaults=code_build_options,
        )
        self.__pipeline.add_stage(deploy_app_stage)

    def add_application_stage(
        self,
        app_stage: Stage,
        *,
        extra_run_order_space: Optional[int] = None,
        manual_approvals: Optional[bool] = None,
    ) -> pipelines.StageDeployment:
        return self.__pipeline.add_stage(
            app_stage,
            extra_run_order_space=extra_run_order_space,
            manual_approvals=manual_approvals,
        )

    def add_stage(
        self,
        stage_name: str,
        *,
        confirm_broadening_permissions: Optional[bool] = None,
        security_notification_topic: Optional[sns.ITopic] = None,
    ) -> pipelines.StageDeployment:
        return self.__pipeline.add_stage(
            stage_name,
            confirm_broadening_permissions=confirm_broadening_permissions,
            security_notification_topic=security_notification_topic,
        )

    def role(self):
        return self.__pipeline.pipeline.role
