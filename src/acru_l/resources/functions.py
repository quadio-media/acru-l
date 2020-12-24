from typing import List, Optional

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python as lambda_python,
    aws_logs as logs,
    aws_s3 as s3,
)


class FunctionWrapper(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        private_bucket: Optional[s3.Bucket] = None,
        secret_arns: Optional[List] = None,
        policy_statements: Optional[List[iam.PolicyStatement]] = None,
    ):
        super().__init__(scope, id)
        self.secret_arns = secret_arns
        self.policy_statements = policy_statements or []
        self.private_bucket = private_bucket

    def setup_function_perms(self):
        if self.secret_arns:
            self.handler.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["secretsmanager:GetSecretValue"],
                    resources=self.secret_arns,
                )
            )
        if self.private_bucket:
            self.handler.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:PutObject",
                        "s3:GetObjectAcl",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:DeleteObject",
                        "s3:PutObjectAcl",
                    ],
                    resources=[
                        f"{self.private_bucket.bucket_arn}/*",
                        self.private_bucket.bucket_arn,
                    ],
                )
            )

        for policy_statement in self.policy_statements:
            self.handler.add_to_role_policy(policy_statement)


class Function(FunctionWrapper):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        source_path: str,
        handler_path: str = "handler.main",
        layers: List[_lambda.LayerVersion],
        runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_8,
        vpc: Optional[ec2.Vpc] = None,
        environment_variables: Optional[dict] = None,
        timeout: core.Duration = core.Duration.seconds(300),
        memory_size: int = 1024,
        log_retention: logs.RetentionDays = logs.RetentionDays.ONE_DAY,
        profiling: bool = False,
        tracing: Optional[_lambda.Tracing] = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        self.handler = _lambda.Function(
            self,
            "Handler",
            code=_lambda.Code.from_asset(source_path),
            handler=handler_path,
            runtime=runtime,
            layers=layers,
            memory_size=memory_size,
            environment=environment_variables,
            timeout=timeout,
            vpc=vpc,
            log_retention=log_retention,
            tracing=tracing,
            profiling=profiling,
        )
        self.setup_function_perms()


class PythonFunction(FunctionWrapper):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        source_path: str,
        index: str = "handler.py",
        handler: str = "main",
        layers: List[_lambda.LayerVersion],
        runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_8,
        vpc: Optional[ec2.Vpc] = None,
        environment_variables: Optional[dict] = None,
        timeout: core.Duration = core.Duration.seconds(300),
        memory_size: int = 1024,
        log_retention: logs.RetentionDays = logs.RetentionDays.ONE_DAY,
        profiling: bool = False,
        tracing: Optional[_lambda.Tracing] = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        self.handler = lambda_python.PythonFunction(
            self,
            "Handler",
            entry=source_path,
            handler=handler,
            index=index,
            runtime=runtime,
            layers=layers,
            memory_size=memory_size,
            environment=environment_variables,
            timeout=timeout,
            vpc=vpc,
            log_retention=log_retention,
            tracing=tracing,
            profiling=profiling,
        )
        self.setup_function_perms()
