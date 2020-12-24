import os

from typing import Optional, List

from aws_cdk import (
    core,
    custom_resources as acr,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python as lambda_python,
)

from acru_l.resources.custom_resources import PythonCustomResource


dirname = os.path.dirname(__file__)


class SES(core.Construct):
    def __init__(
        self, scope: core.Construct, id: str, *, emails: Optional[List[str]]
    ):
        super().__init__(scope, id)

        ses_config_layer = lambda_python.PythonLayerVersion(
            scope,
            "SESConfigLayer",
            entry=os.path.join(dirname, "layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8],
        )

        PythonCustomResource(
            self,
            "SESDomainValidation",
            source_dir=os.path.join(dirname, "domain_validation"),
            handler="on_event",
            environment={
                "DOMAIN": self.hosted_zone.zone_name,
                "HOSTED_ZONE_ID": self.hosted_zone.hosted_zone_id,
            },
            layers=[
                ses_config_layer,
            ],
            policy_statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ses:VerifyDomainDkim",
                        "ses:VerifyDomainIdentity",
                    ],
                    resources=acr.AwsCustomResourcePolicy.ANY_RESOURCE,
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["route53:ChangeResourceRecordSets"],
                    resources=[self.hosted_zone.hosted_zone_arn],
                ),
            ],
        )

        emails = emails or []
        PythonCustomResource(
            self,
            "SESVerifyEmails",
            source_dir=os.path.join(dirname, "ses_verified_emails"),
            handler="on_event",
            layers=[
                ses_config_layer,
            ],
            policy_statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["ses:VerifyEmailIdentity"],
                    resources=acr.AwsCustomResourcePolicy.ANY_RESOURCE,
                )
            ],
            resource_properties={"emails": emails},
        )
