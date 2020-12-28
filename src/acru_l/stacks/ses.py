from aws_cdk import core, aws_route53 as route53

from acru_l.resources.ses import SESVerification
from acru_l.stacks.base import BaseStack
from acru_l.stacks.config import SESConfig


class EmailsStack(BaseStack):

    config_class = SESConfig
    config: SESConfig

    def __init__(
        self, scope: core.Construct, id: str, env: core.Environment, **kwargs
    ):
        super().__init__(scope, id, env=env, **kwargs)
        config = self.config
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=config.hosted_zone_domain_name
        )
        SESVerification(
            self, "Verification", hosted_zone=hosted_zone, emails=config.emails
        )
