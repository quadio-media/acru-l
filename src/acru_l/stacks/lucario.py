from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_certificatemanager as acm,
    aws_route53 as route53,
)

from acru_l.resources.rds.instances import PostgresInstance
from acru_l.services.wsgi import WSGIService
from acru_l.stacks.base import BaseStack
from acru_l.stacks.config import APIConfig, CanaryConfig


class LucarioStack(BaseStack):
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

    config_class = APIConfig
    config: APIConfig

    def __init__(
        self, scope: core.Construct, id: str, env: core.Environment, **kwargs
    ):
        super().__init__(scope, id, env=env, **kwargs)

        config = self.config
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=config.vpc_name)
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=config.hosted_zone_domain_name
        )

        db_config = config.rds_config
        database = PostgresInstance(
            self,
            f"{id}PG",
            db_name=db_config.db_name,
            db_username=db_config.db_username,
            vpc=vpc,
            multi_az=db_config.multi_az,
            deletion_protection=db_config.deletion_protection,
            instance_type=db_config.instance_type,
        )
        if db_config.setup_alarms:
            database.setup_alarms()

        # TODO: Add options for Redis Elasticache
        service_config = config.service_config
        environment_variables = service_config.environment or {}
        environment_variables.update(
            {
                "DB_NAME": database.db_name,
                "DB_USERNAME": database.db_username,
                "DB_HOST": database.endpoint_address,
                "DB_PORT": database.endpoint_port,
                "DB_SECRET_ID": database.creds.secret_arn,
            }
        )

        secret_arns = [database.creds.secret_arn]

        certificate = acm.Certificate.from_certificate_arn(
            self,
            f"{id}Certificate",
            core.Fn.import_value(config.cert_export_name),
        )
        canary_config = None
        if service_config.health_check_url:
            canary_config = CanaryConfig(
                commit_sha=self.commit_sha,
                version=config.version,
                health_check_url=service_config.health_check_url,
            )
        self.service = WSGIService(
            self,
            f"{id}Service",
            vpc=vpc,
            certificate=certificate,
            hosted_zone=hosted_zone,
            domain_name=service_config.domain_name,
            environment_variables=environment_variables,
            secret_arns=secret_arns,
            project_source_path=service_config.project_source_path,
            pre_deploy_config=service_config.pre_deploy_config,
            post_deploy_config=service_config.post_deploy_config,
            canary_config=canary_config,
            secrets=service_config.secrets,
        )
