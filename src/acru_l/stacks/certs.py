from typing import List, Optional

from aws_cdk import core, aws_certificatemanager as acm, aws_route53 as route53
from pydantic import BaseModel

from acru_l.core import Stack, StackFactory
from acru_l.resources.hosted_zone import HostedZone


class HostedZoneOptions(BaseModel):
    domain_name: str
    export_name: str
    use_github_pages: bool = False
    github_username: Optional[str] = None
    github_cname: Optional[str] = None

    def build(self, scope: core.Construct, id: str):
        return HostedZone(
            scope,
            id,
            domain_name=self.domain_name,
            export_name=self.export_name,
            use_github_pages=self.use_github_pages,
            github_username=self.github_username,
            github_cname=self.github_cname,
        )


class CertOptions(BaseModel):
    name: str
    domain_name: str
    export_name: str


class CertsOptions(BaseModel):
    hosted_zone_domain_name: str
    certificates: List[CertOptions]


class CertificatesStack(Stack):
    def build(self, options: CertsOptions):
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=options.hosted_zone_domain_name
        )
        for cert_options in options.certificates:
            cert = acm.DnsValidatedCertificate(
                self,
                cert_options.name,
                domain_name=cert_options.domain_name,
                hosted_zone=hosted_zone,
            )
            core.CfnOutput(
                self,
                f"{cert_options.name}Output",
                value=cert.certificate_arn,
                export_name=cert_options.export_name,
            )


class CertificatesStackFactory(StackFactory):
    stack_class = CertificatesStack
    options_class = CertsOptions
