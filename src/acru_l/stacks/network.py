from acru_l.resources.hosted_zone import HostedZone
from acru_l.resources.vpc import VPC
from acru_l.stacks.base import BaseStack
from aws_cdk import (
    core,
)

from acru_l.stacks.config import NetworkConfig


class NetworkStack(BaseStack):

    config_class = NetworkConfig
    config: NetworkConfig

    def __init__(
        self, scope: core.Construct, id: str, env: core.Environment, **kwargs
    ):
        super().__init__(scope, id, env=env, **kwargs)
        config = self.config
        VPC(
            self,
            "VPC",
            cidr=config.vpc.cidr,
            export_name=config.vpc.export_name,
        )
        HostedZone(
            self,
            "HostedZone",
            domain_name=config.hosted_zone.domain_name,
            export_name=config.hosted_zone.export_name,
            use_github_pages=config.hosted_zone.use_github_pages,
        )
