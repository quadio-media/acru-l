from aws_cdk import (
    core,
    aws_ec2 as ec2,
)


class VPC(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        cidr: str = "10.1.0.0/16",
        export_name: str = "VpcId"
    ):
        super().__init__(scope, id)

        subnet0 = ec2.SubnetConfiguration(
            name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
        )
        subnet1 = ec2.SubnetConfiguration(
            name="Private", subnet_type=ec2.SubnetType.PRIVATE, cidr_mask=24
        )

        vpc = ec2.Vpc(
            self,
            "VPC",
            cidr=cidr,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateways=1,
            subnet_configuration=[
                subnet0,
                subnet1,
            ],
        )
        # Usage: core.Fn.import_value('VpcId')
        core.CfnOutput(
            self, "VpcId", value=vpc.vpc_id, export_name=export_name
        )
