from aws_cdk import Stack
from constructs import Construct

from aws_cdk import (
    pipelines as pipelines
)

class PipelineStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        pipeline = pipelines.CodePipeline(self, "Pipeline",
            pipeline_name="MoodMePipeline",
            synth=pipelines.ShellStep("Synth",
                input=pipelines.CodePipelineSource.git_hub("moodme/moodme", "main", authentication=[])
                )
            )

