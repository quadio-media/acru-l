from aws_cdk import core, aws_certificatemanager as acm, aws_route53 as route53

from acru_l.stacks.base import BaseStack
from acru_l.stacks.config import CertConfig


class CertificatesStack(BaseStack):
    config_class = CertConfig
    config: CertConfig

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        env: core.Environment,
        **kwargs,
    ):
        super().__init__(scope, id, env=env, **kwargs)
        config = self.config
        subdomains = config.subdomains or []
        domain_name = config.domain_name
        export_prefix = config.export_prefix
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=domain_name
        )
        main_cert = acm.DnsValidatedCertificate(
            self,
            "MainCertificate",
            domain_name=domain_name,
            hosted_zone=hosted_zone,
        )
        core.CfnOutput(
            self,
            "MainCertificateARN",
            value=main_cert.certificate_arn,
            export_name=f"{export_prefix.title()}MainCertificate",
        )
        wild_cert = acm.DnsValidatedCertificate(
            self,
            "WildCardCertificate",
            domain_name=f"*.{domain_name}",
            hosted_zone=hosted_zone,
        )
        core.CfnOutput(
            self,
            "WildCardCertificateARN",
            value=wild_cert.certificate_arn,
            export_name=f"{export_prefix.title()}WildCardCertificate",
        )
        for subdomain in subdomains:
            prefix_wild_cert = acm.DnsValidatedCertificate(
                self,
                f"{subdomain.title()}WildCardCertificate",
                domain_name=f"*.{subdomain.lower()}.{domain_name}",
                hosted_zone=hosted_zone,
            )
            _prefix = subdomain.title() + export_prefix.title()
            core.CfnOutput(
                self,
                f"{subdomain.title()}WildCardCertificateARN",
                value=prefix_wild_cert.certificate_arn,
                export_name=f"{_prefix}WildCardCertificate",
            )
