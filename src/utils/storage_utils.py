import os
from core.common import get_settings
settings = get_settings()

def get_model_dir(model_name: str, version: str) -> str:
    return f"{settings.MODEL_PATH}/{model_name}/{version}"

def is_model_present(model_name: str, version: str) -> bool:
    return os.path.exists(get_model_dir(model_name, version))

