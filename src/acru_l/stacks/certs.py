from typing import List, Optional

from aws_cdk import core, aws_certificatemanager as acm, aws_route53 as route53
from pydantic import BaseModel, Field

from acru_l.core import Stack, StackFactory
from acru_l.resources.hosted_zone import HostedZone


class HostedZoneFactory(BaseModel):
    name: str
    domain_name: str
    export_name: str
    use_github_pages: bool = False
    github_username: Optional[str] = None
    github_cname: Optional[str] = None

    def build(self, scope: core.Construct):
        return HostedZone(
            scope,
            self.name,
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

    def build(self, scope: core.Construct, hosted_zone: route53.HostedZone):
        cert = acm.DnsValidatedCertificate(
            scope,
            self.name,
            domain_name=self.domain_name,
            hosted_zone=hosted_zone,
        )
        core.CfnOutput(
            scope,
            f"{self.name}Output",
            value=cert.certificate_arn,
            export_name=self.export_name,
        )


class CertsFactory(BaseModel):
    name: Optional[str] = None
    hosted_zone_domain_name: Optional[str] = None
    hosted_zone: Optional[HostedZoneFactory] = None
    certificates: List[CertOptions] = Field(default_factory=list)

    def build(self, scope: core.Construct):
        if self.hosted_zone:
            hosted_zone = self.hosted_zone.build(scope)
        else:
            hosted_zone = route53.HostedZone.from_lookup(
                scope, self.name, domain_name=self.hosted_zone_domain_name
            )

        for cert_options in self.certificates:
            cert_options.build(scope, hosted_zone)


class CertsOptions(BaseModel):
    hosted_zones: List[CertsFactory] = Field(default_factory=list)


class CertificatesStack(Stack):
    def build(self, options: CertsOptions):
        for factory in options.hosted_zones:
            factory.build(self)


class CertificatesStackFactory(StackFactory):
    stack_class = CertificatesStack
    options_class = CertsOptions
