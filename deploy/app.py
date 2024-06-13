#!/usr/bin/env python3
import os

import datetime as dt
import yaml
import os

from aws_cdk import (
    App, Environment
)

from deploy.moodme_stack import MoodMeStack
from deploy.utils import get_from_config_environ_or_default

account = get_from_config_environ_or_default('account', '')
region = get_from_config_environ_or_default('region', '')
description = get_from_config_environ_or_default('description', '')

deletion_date = (dt.datetime.utcnow() + dt.timedelta(days=90)).strftime('%Y%m%dT%H%M%SZ')

tag_dict = {'moodme:deletion-date': deletion_date}

env = Environment(account=account, region=region)
print(env)
app = App()

MoodMeStack(app, "DeployStack",
    env=env,
    tags=tag_dict,
    description=description
    )

app.synth()
