from aws_cdk import (
    core,
)


class BaseStack(core.Stack):

    config_class = NotImplemented

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        env: core.Environment,
        *,
        commit_sha: str,
        config,
        **kwargs
    ):
        super().__init__(scope, id, env=env, **kwargs)
        self.commit_sha = commit_sha
        self.config = config
