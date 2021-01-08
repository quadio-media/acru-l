from typing import Optional

from pydantic import BaseModel

from acru_l.core import Stack, StackFactory
from acru_l.resources.vpc import VPC
from acru_l.stacks.certs import HostedZoneFactory


class VpcOptions(BaseModel):
    name: str
    cidr: str
    export_name: str


class NetworkOptions(BaseModel):
    vpc: VpcOptions
    hosted_zone: Optional[HostedZoneFactory] = None


class NetworkStack(Stack):
    def build(self, options: NetworkOptions):
        VPC(
            self,
            "VPC",
            name=options.vpc.name,
            cidr=options.vpc.cidr,
            export_name=options.vpc.export_name,
        )
        if options.hosted_zone is not None:
            options.hosted_zone.build(self)


class NetworkStackFactory(StackFactory):
    stack_class = NetworkStack
    options_class = NetworkOptions
