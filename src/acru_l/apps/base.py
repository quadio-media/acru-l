#!/usr/bin/env python3
import toml
from aws_cdk import (
    core,
)
from pydantic import BaseSettings
from pydantic.utils import import_string
from typing import Optional

# from acrul_toolkit.module_loading import import_string


class AppConfig(BaseSettings):
    AWS_ACCOUNT_ID: str
    AWS_REGION: str
    COMMIT_SHA: str
    CONFIG_FILE_PATH: str = "./acru_l.toml"

    class Config:
        case_sensitive = True


def setup_app(
    app: Optional[core.App] = None, app_config: Optional[AppConfig] = None
) -> core.App:
    app = app or core.App()
    app_config = app_config or AppConfig()
    env = core.Environment(
        account=app_config.AWS_ACCOUNT_ID, region=app_config.AWS_REGION
    )
    config_dict = toml.load(app_config.CONFIG_FILE_PATH)
    for stack in config_dict["stack"]:
        stack_class = import_string(stack["stack_class"])
        stack_config_class = stack_class.config_class
        stack_class(
            app,
            stack["name"],
            env=env,
            commit_sha=app_config.COMMIT_SHA,
            config=stack_config_class(**stack["config"]),
        )
    return app
