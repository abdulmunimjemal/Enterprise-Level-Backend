import yaml
from os import environ, path
import re


def get_from_config_environ_or_default(key: str, default: str, **kwargs) -> str:
    if 'CDK_STACK_CONFIG' not in environ:
        environ['CDK_STACK_CONFIG'] = path.join(
            path.dirname(__file__), "..", 'config.yml')

    with open(environ['CDK_STACK_CONFIG'], 'r') as stream:
        config = yaml.safe_load(stream)

    if key in config:
        return config[key]
    elif kwargs is not None and 'default' in kwargs:
        return kwargs['default']
    else:
        return default


def clean_name(branch: str):
    return re.sub("/", "-", branch)[0:30]
