import os
from typing import Mapping, Any, Optional, List, Dict

from aws_cdk import (
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_route53 as route53,
    aws_s3 as s3,
)
from aws_cdk import core, aws_secretsmanager as secretsmanager
from aws_cdk.aws_ec2 import IConnectable
from pydantic import BaseModel, Field

from acru_l.resources.apigateway import LambdaAPIGateway
from acru_l.resources.canary import Canary
from acru_l.resources.custom_resources import CustomResource
from acru_l.resources.functions import Function


class SecretsOptions(BaseModel):
    name: str
    arn_key: str
    exclude_punctuation: bool = True
    include_space: bool = False
    password_length: int = 32

    def create(self, *, scope: core.Construct) -> secretsmanager.Secret:
        return secretsmanager.Secret(
            scope,
            self.name,
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=self.exclude_punctuation,
                include_space=self.include_space,
                password_length=self.password_length,
            ),
        )


class CanaryOptions(BaseModel):

    deploy_id: str
    version: str
    health_check_url: str


class CustomResourceOptions(BaseModel):

    source_path: str
    properties: Mapping[str, Any]


class ServiceOptions(BaseModel):
    domain_name: str
    project_source_path: str
    api_lambda_source_path: Optional[str] = None
    secrets: Optional[List[SecretsOptions]] = Field(default_factory=list)
    secret_arns: Optional[List[str]] = Field(default_factory=list)
    local_environment: Optional[List[str]] = Field(default_factory=list)
    environment: Optional[Dict[str, Any]] = Field(default_factory=dict)
    health_check_url: Optional[str] = None
    pre_deploy_options: Optional[CustomResourceOptions] = None
    post_deploy_options: Optional[CustomResourceOptions] = None


class Service(core.Construct):

    pre_deploy: Optional[CustomResource] = None
    post_deploy: Optional[CustomResource] = None
    canary: Optional[Canary] = None
    layers: List[_lambda.LayerVersion]
    api_lambda: Function
    apigw: LambdaAPIGateway

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        options: ServiceOptions,
        certificate: acm.Certificate,
        hosted_zone: route53.HostedZone,
        deploy_id: str,
        version: str,
        vpc: Optional[ec2.Vpc] = None,
        function_class=Function,
        runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_8,
    ):
        super().__init__(scope, id)
        self.function_class = function_class
        self.private_bucket = s3.Bucket(
            self, "PrivateBucket", public_read_access=False
        )
        self.vpc = vpc
        self.runtime = runtime
        self.environment_variables = options.environment
        self.secret_arns = options.secret_arns

        self.setup_environment(
            secrets=options.secrets,
            local_environment_variables=options.local_environment,
        )
        self.layers = self.package_project(
            source_path=options.project_source_path
        )

        self.add_pre_deploy(options=options.pre_deploy_options)
        self.add_api(
            api_lambda_source_path=options.api_lambda_source_path,
            domain_name=options.domain_name,
            certificate=certificate,
            hosted_zone=hosted_zone,
        )
        canary_options = None
        if options.health_check_url:
            canary_options = CanaryOptions(
                deploy_id=deploy_id,
                version=version,
                health_check_url=options.health_check_url,
            )
        self.add_canary(options=canary_options)
        self.add_post_deploy(options=options.post_deploy_options)

    def setup_environment(
        self,
        *,
        secrets: Optional[List[SecretsOptions]],
        local_environment_variables: Optional[List[str]],
    ):
        secrets = secrets or []
        for secrets_options in secrets:
            _secret = secrets_options.create(scope=self)
            envvar_id = secrets_options.arn_key.upper()
            self.secret_arns.append(_secret.secret_arn)
            self.environment_variables[envvar_id] = _secret.secret_arn

        names = local_environment_variables or []
        for name in names:
            self.environment_variables[name] = os.environ[name]

        bucket_name = self.private_bucket.bucket_name
        self.environment_variables["PRIVATE_S3_BUCKET_NAME"] = bucket_name

    def package_project(
        self, *, source_path: str
    ) -> List[_lambda.LayerVersion]:
        project_layer = _lambda.LayerVersion(
            self,
            "ProjectLayer",
            code=_lambda.Code.from_asset(source_path),
            compatible_runtimes=[self.runtime],
        )
        return [project_layer]

    def make_function(self, name: str, **kwargs):
        return self.function_class(
            self,
            name,
            layers=self.layers,
            private_bucket=self.private_bucket,
            secret_arns=self.secret_arns,
            environment_variables=self.environment_variables,
            vpc=self.vpc,
            runtime=self.runtime,
            **kwargs,
        )

    def add_api(
        self,
        *,
        api_lambda_source_path: str,
        domain_name: str,
        certificate: acm.Certificate,
        hosted_zone: route53.HostedZone,
    ):
        self.api_lambda = self.make_function(
            "MainLambda",
            source_path=api_lambda_source_path,
            profiling=True,
            tracing=_lambda.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.THREE_MONTHS,
        )
        if self.pre_deploy:
            self.api_lambda.handler.node.add_dependency(
                self.pre_deploy.resource
            )

        keep_warm = events.Rule(
            self, "KeepWarm", schedule=events.Schedule.cron(minute="*/5")
        )
        keep_warm.add_target(
            targets.LambdaFunction(handler=self.api_lambda.handler)
        )

        self.apigw = LambdaAPIGateway(
            self,
            "APIGW",
            domain_name=domain_name,
            certificate=certificate,
            handler=self.api_lambda.handler,
            hosted_zone=hosted_zone,
        )

    def add_canary(self, *, options: Optional[CanaryOptions]):
        if options:
            self.canary = Canary(
                self,
                "Canary",
                deploy_id=options.deploy_id,
                version=options.version,
                health_check_url=options.health_check_url,
            )
            self.canary.add_dependency(self.api_lambda.handler)

    def add_pre_deploy(self, *, options: Optional[CustomResourceOptions]):
        if options:
            pre_deploy_lambda = self.make_function(
                "PreDeployLambda", source_path=options.source_path
            )

            self.pre_deploy = CustomResource(
                self,
                "PreDeploy",
                on_event_handler=pre_deploy_lambda.handler,
                resource_properties=options.properties,
            )

    def add_post_deploy(self, *, options: Optional[CustomResourceOptions]):
        if options:
            post_deploy_lambda = self.make_function(
                "PostDeployLambda", source_path=options.source_path
            )

            self.post_deploy = CustomResource(
                self,
                "PostDeploy",
                on_event_handler=post_deploy_lambda.handler,
                resource_properties=options.properties,
            )
            if self.canary:
                self.post_deploy.resource.node.add_dependency(
                    self.canary.resource
                )
            else:
                self.post_deploy.resource.node.add_dependency(
                    self.api_lambda.handler
                )

    def allow_connection_to(self, other: IConnectable, port_range: ec2.Port):
        if self.pre_deploy:
            other.connections.allow_from(
                self.pre_deploy.on_event_handler, port_range
            )
        if self.post_deploy:
            other.connections.allow_from(
                self.post_deploy.on_event_handler, port_range
            )
        other.connections.allow_from(self.api_lambda.handler, port_range)
