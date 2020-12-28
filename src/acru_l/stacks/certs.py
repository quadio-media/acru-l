from aws_cdk import core, aws_certificatemanager as acm, aws_route53 as route53

from acru_l.stacks.base import BaseStack
from acru_l.stacks.config import CertsConfig


class CertificatesStack(BaseStack):
    config_class = CertsConfig
    config: CertsConfig

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        env: core.Environment,
        **kwargs,
    ):
        super().__init__(scope, id, env=env, **kwargs)
        config = self.config
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=config.hosted_zone_domain_name
        )
        for cert_config in config.certificates:
            cert = acm.DnsValidatedCertificate(
                self,
                cert_config.name,
                domain_name=cert_config.domain_name,
                hosted_zone=hosted_zone,
            )
            core.CfnOutput(
                self,
                f"{cert_config.name}Output",
                value=cert.certificate_arn,
                export_name=cert_config.export_name,
            )
