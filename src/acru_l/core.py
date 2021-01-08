from typing import Type, Optional, Mapping, Dict, List, Any

import pydantic
import toml
from aws_cdk import core

from acru_l.utils import traverse


class Settings(pydantic.BaseSettings):

    AWS_ACCOUNT_ID: str
    AWS_REGION: str
    DEPLOY_ID: str
    ACRUL_CONFIG_PATH: pydantic.FilePath = "./acru-l.toml"
    ACRUL_SECTION: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def env(self):
        return core.Environment(
            account=self.AWS_ACCOUNT_ID, region=self.AWS_REGION
        )

    @property
    def config(self):
        data = toml.load(self.ACRUL_CONFIG_PATH)
        if self.ACRUL_SECTION:
            data = traverse(data, self.ACRUL_SECTION)
        return AcrulConfig(**data)


class StackConfig(pydantic.BaseModel):

    id: str
    factory: pydantic.PyObject
    options: Optional[Dict]

    analytics_reporting: Optional[bool] = None
    description: Optional[str] = None
    name: Optional[str] = None
    synthesizer: Optional[pydantic.PyObject] = None
    tags: Optional[Mapping[str, str]] = None
    termination_protection: Optional[bool] = None


class AppConfig(pydantic.BaseModel):
    analytics_reporting: Optional[bool] = None
    auto_synth: Optional[bool] = None
    context: Optional[Mapping[str, Any]] = None
    outdir: Optional[str] = None
    runtime_info: Optional[bool] = None
    stack_traces: Optional[bool] = None
    tree_metadata: Optional[bool] = None


class AcrulConfig(pydantic.BaseModel):
    app: AppConfig = AppConfig()
    stacks: List[StackConfig]


def app_factory(
    account: Optional[str] = None,
    region: Optional[str] = None,
    deploy_id: Optional[str] = None,
    config_path: Optional[str] = None,
    section: Optional[str] = None,
) -> "App":
    default_settings = {}
    if account:
        default_settings["AWS_ACCOUNT_ID"] = account
    if region:
        default_settings["AWS_REGION"] = region
    if deploy_id:
        default_settings["DEPLOY_ID"] = deploy_id
    if config_path:
        default_settings["ACRUL_CONFIG_PATH"] = config_path
    if section:
        default_settings["ACRUL_SECTION"] = section

    settings = Settings(**default_settings)
    env = settings.env
    config = settings.config
    app = App(
        analytics_reporting=config.app.analytics_reporting,
        auto_synth=config.app.auto_synth,
        context=config.app.context,
        outdir=config.app.outdir,
        runtime_info=config.app.runtime_info,
        stack_traces=config.app.stack_traces,
        tree_metadata=config.app.tree_metadata,
    )

    for stack in config.stacks:
        app.add_stack(
            stack.factory(),
            stack.id,
            deploy_id=settings.DEPLOY_ID,
            env=env,
            description=stack.description,
            analytics_reporting=stack.analytics_reporting,
            stack_name=stack.name,
            synthesizer=stack.synthesizer,
            tags=stack.tags,
            termination_protection=stack.termination_protection,
            options=stack.options,
        )

    return app


class App(core.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stacks = {}

    def add_stack(
        self,
        stack_factory: "StackFactory",
        id: str,
        *,
        deploy_id: str,
        analytics_reporting: Optional[bool] = None,
        description: Optional[str] = None,
        env: Optional[core.Environment] = None,
        stack_name: Optional[str] = None,
        synthesizer: Optional[core.IStackSynthesizer] = None,
        tags: Optional[Mapping[str, str]] = None,
        termination_protection: Optional[bool] = None,
        options: Optional[Dict] = None
    ) -> "Stack":
        self._stacks[id] = stack_factory.build(
            self,
            id,
            deploy_id=deploy_id,
            analytics_reporting=analytics_reporting,
            description=description,
            env=env,
            stack_name=stack_name,
            synthesizer=synthesizer,
            tags=tags,
            termination_protection=termination_protection,
            options=options,
        )
        return self._stacks[id]


class Stack(core.Stack):
    """
    Usage:
        class MyStack(Stack):

            def build(self, options: MyOptionsClass):
                ...


        app = App()
        add.add_stack(
            MyStack,
            "MyStackId",

    """

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        deploy_id: str,
        analytics_reporting: Optional[bool] = None,
        description: Optional[str] = None,
        env: Optional[core.Environment] = None,
        stack_name: Optional[str] = None,
        synthesizer: Optional[core.IStackSynthesizer] = None,
        tags: Optional[Mapping[str, str]] = None,
        termination_protection: Optional[bool] = None,
        options: Optional[pydantic.BaseModel] = None
    ):
        super().__init__(
            scope,
            id,
            env=env,
            analytics_reporting=analytics_reporting,
            description=description,
            stack_name=stack_name,
            synthesizer=synthesizer,
            tags=tags,
            termination_protection=termination_protection,
        )
        self.deploy_id = deploy_id
        self.build(options=options)

    def build(self, options: pydantic.BaseModel):
        pass  # pragma: no cover


class StackFactory:
    stack_class: Type[Stack]
    options_class: Type[pydantic.BaseModel]

    def build(
        self,
        scope: core.Construct,
        id: str,
        *,
        deploy_id: str,
        analytics_reporting: Optional[bool] = None,
        description: Optional[str] = None,
        env: Optional[core.Environment] = None,
        stack_name: Optional[str] = None,
        synthesizer: Optional[core.IStackSynthesizer] = None,
        tags: Optional[Mapping[str, str]] = None,
        termination_protection: Optional[bool] = None,
        options: Optional[Dict] = None
    ) -> Stack:
        return self.stack_class(
            scope,
            id,
            deploy_id=deploy_id,
            env=env,
            analytics_reporting=analytics_reporting,
            description=description,
            stack_name=stack_name,
            synthesizer=synthesizer,
            tags=tags,
            termination_protection=termination_protection,
            options=self.options_class(**options) if options else None,
        )
