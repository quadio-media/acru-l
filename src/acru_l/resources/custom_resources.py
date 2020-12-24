from typing import Mapping, Any, List, Optional

from aws_cdk import (
    core,
    custom_resources as acr,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
)


class CustomResource(core.Construct):

    provider: acr.Provider
    resource: core.CustomResource

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        on_event_handler: Optional[_lambda.Function],
        policy_statements: Optional[List[iam.PolicyStatement]] = None,
        resource_properties: Optional[Mapping[str, Any]] = None,
    ):
        super().__init__(scope, id)
        self.policy_statements = policy_statements or []
        self.resource_properties = resource_properties or {}
        self.on_event_handler = on_event_handler
        if self.on_event_handler is not None:
            self.setup_resource()

    def setup_resource(self):
        for policy_statement in self.policy_statements:
            self.on_event_handler.add_to_role_policy(policy_statement)

        self.provider = acr.Provider(
            self,
            "Provider",
            on_event_handler=self.on_event_handler,
            log_retention=logs.RetentionDays.ONE_DAY,
        )

        self.resource = core.CustomResource(
            self,
            "Resource",
            service_token=self.provider.service_token,
            properties=self.resource_properties,
        )


class PythonCustomResource(CustomResource):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        source_dir: str = None,
        index: str = "handler.py",
        handler: str = "main",
        runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_8,
        layers: Optional[List[_lambda.LayerVersion]] = None,
        environment: Optional[Mapping[str, Any]] = None,
        timeout: core.Duration = core.Duration.seconds(300),
        memory_size: int = 1024,
        log_retention: logs.RetentionDays = logs.RetentionDays.ONE_DAY,
        vpc: Optional[ec2.Vpc] = None,
        **kwargs,
    ):
        kwargs["on_event_handler"] = None
        super().__init__(scope, id, **kwargs)
        environment = environment or {}
        self.on_event_handler = lambda_python.PythonFunction(
            self,
            "OnEventHandler",
            entry=source_dir,
            index=index,
            handler=handler,
            runtime=runtime,
            layers=layers,
            memory_size=memory_size,
            environment=environment,
            timeout=timeout,
            vpc=vpc,
            log_retention=log_retention,
        )
        self.setup_resource()
