from typing import List, Optional

from aws_cdk import aws_route53 as route53
from pydantic import BaseModel

from acru_l.core import Stack, StackFactory
from acru_l.resources.ses import SESVerification


class SESOptions(BaseModel):
    hosted_zone_domain_name: str
    emails: Optional[List[str]] = None


class EmailsStack(Stack):
    def build(self, options: SESOptions):
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=options.hosted_zone_domain_name
        )
        SESVerification(
            self,
            "Verification",
            hosted_zone=hosted_zone,
            emails=options.emails,
        )


class EmailsStackFactory(StackFactory):
    stack_class = EmailsStack
    options_class = SESOptions
