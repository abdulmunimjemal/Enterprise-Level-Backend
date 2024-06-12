from fastapi import BackgroundTasks

from db.models.ai_models import AiModel
from utils.net_utils import download_file


async def download_model(model: AiModel, background_tasks: BackgroundTasks):
    background_tasks.add_task(download_in_the_background, model)


def download_in_the_background(model: AiModel):
    pass

