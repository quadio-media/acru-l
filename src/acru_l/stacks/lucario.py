from typing import Optional

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_certificatemanager as acm,
    aws_route53 as route53,
)
from pydantic import BaseModel

from acru_l.core import Stack, StackFactory
from acru_l.resources.rds.instances import PostgresInstance, RDSInstanceOptions
from acru_l.services.api.base import ServiceOptions
from acru_l.services.api.wsgi import WSGIService


class LucarioOptions(BaseModel):
    hosted_zone_domain_name: str
    cert_export_name: str
    version: str
    vpc_name: str
    service_options: ServiceOptions
    rds_options: Optional[RDSInstanceOptions]


class LucarioStack(Stack):
    """
    WSGI
    POSTGRES
    LAMBDA
    API GATEWAY

    TODO: add REDIS

    Prerequisites:
    VPC
    HOSTED_ZONE
    CERTIFICATES
    """

    service: WSGIService

    def build(self, options: LucarioOptions):
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=options.vpc_name)
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=options.hosted_zone_domain_name
        )

        service_options = options.service_options

        db_options = options.rds_options
        database = None
        if db_options is not None:
            database = PostgresInstance(
                self, "PG", vpc=vpc, options=db_options
            )

            service_options.environment.update(
                {
                    "DB_NAME": database.db_name,
                    "DB_USERNAME": database.db_username,
                    "DB_HOST": database.endpoint_address,
                    "DB_PORT": database.endpoint_port,
                    "DB_SECRET_ID": database.creds.secret_arn,
                }
            )
            service_options.secret_arns += [database.creds.secret_arn]

        # TODO: Add options for Redis Elasticache

        certificate = acm.Certificate.from_certificate_arn(
            self,
            "Certificate",
            core.Fn.import_value(options.cert_export_name),
        )
        self.service = WSGIService(
            self,
            "Service",
            vpc=vpc,
            certificate=certificate,
            hosted_zone=hosted_zone,
            version=options.version,
            deploy_id=self.deploy_id,
            options=service_options,
        )
        # TODO: add dependency from db to service so that the build happens
        #       in the right order.
        # if database:
        #     self.service.allow_connection_to(
        #         database.connection_interface,
        #         ec2.Port.tcp(database.port)
        #     )


class LucarioStackFactory(StackFactory):
    stack_class = LucarioStack
    options_class = LucarioOptions
