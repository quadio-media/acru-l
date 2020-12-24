from aws_cdk import (
    core,
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_route53 as route53,
    aws_s3 as s3,
)
from typing import Optional, List

from acru_l.resources.apigateway import LambdaAPIGateway
from acru_l.resources.canary import Canary
from acru_l.resources.custom_resources import CustomResource
from acru_l.resources.functions import Function
from acru_l.stacks.config import (
    SecretsConfig,
    CustomResourceConfig,
    CanaryConfig,
)


class Service(core.Construct):

    pre_deploy: Optional[CustomResource] = None
    post_deploy: Optional[CustomResource] = None
    canary: Optional[Canary]
    layers: List[_lambda.LayerVersion]
    api_lambda: Function
    apigw: LambdaAPIGateway

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        domain_name: str,
        project_source_path: str,
        api_lambda_source_path: str,
        certificate: acm.Certificate,
        hosted_zone: route53.HostedZone,
        runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_8,
        vpc: Optional[ec2.Vpc] = None,
        environment_variables: Optional[dict] = None,
        secrets: Optional[List[SecretsConfig]] = None,
        secret_arns: Optional[List] = None,
        function_class=Function,
        pre_deploy_config: CustomResourceConfig,
        post_deploy_config: CustomResourceConfig,
        canary_config: CanaryConfig,
    ):
        super().__init__(scope, id)
        self.function_class = function_class
        self.private_bucket = s3.Bucket(
            self, "PrivateBucket", public_read_access=False
        )
        self.vpc = vpc
        self.runtime = runtime
        self.environment_variables = environment_variables or {}
        self.secret_arns = secret_arns or []

        self.setup_environment(secrets=secrets)
        self.layers = self.package_project(source_path=project_source_path)

        self.add_pre_deploy(config=pre_deploy_config)
        self.add_api(
            api_lambda_source_path=api_lambda_source_path,
            domain_name=domain_name,
            certificate=certificate,
            hosted_zone=hosted_zone,
        )
        self.add_canary(config=canary_config)
        self.add_post_deploy(config=post_deploy_config)

    def setup_environment(self, *, secrets: Optional[List[SecretsConfig]]):
        secrets = secrets or []
        for secrets_config in secrets:
            _secret = secrets_config.create(scope=self)
            envvar_id = f"{secrets_config.arn_key.upper()}_ID"
            self.secret_arns.append(_secret.secret_arn)
            self.environment_variables[envvar_id] = _secret.secret_arn

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

    def add_canary(self, *, config: CanaryConfig):
        self.canary = Canary(
            self,
            "Canary",
            commit_sha=config.commit_sha,
            version=config.version,
            health_check_url=config.health_check_url,
        )
        self.canary.add_dependency(self.api_lambda.handler)

    def add_pre_deploy(self, *, config: CustomResourceConfig):
        pre_deploy_lambda = self.make_function(
            "PreDeployLambda", source_path=config.source_path
        )

        self.pre_deploy = CustomResource(
            self,
            "PreDeploy",
            on_event_handler=pre_deploy_lambda.handler,
            resource_properties=config.properties,
        )

    def add_post_deploy(self, *, config: CustomResourceConfig):
        post_deploy_lambda = self.make_function(
            "PostDeployLambda", source_path=config.source_path
        )

        self.post_deploy = CustomResource(
            self,
            "PostDeploy",
            on_event_handler=post_deploy_lambda.handler,
            resource_properties=config.properties,
        )
        if self.canary:
            self.post_deploy.resource.node.add_dependency(self.canary.resource)
        else:
            self.post_deploy.resource.node.add_dependency(
                self.api_lambda.handler
            )
