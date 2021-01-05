import os

from aws_cdk import (
    core,
    aws_sns as sns,
    aws_iam as iam,
)

from acru_l.resources.custom_resources import PythonCustomResource


dirname = os.path.dirname(__file__)


class SESConfigurationSet(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        name: str,
        destination_name: str
    ):
        super().__init__(scope, id)
        configuration_set_topic = sns.Topic(self, "Topic")

        PythonCustomResource(
            self,
            "ConfigurationSet",
            source_dir=os.path.join(dirname, "configuration_set"),
            environment={
                "CONFIGURATION_SET_NAME": name,
                "EVENT_DESTINATION_NAME": destination_name,
            },
            resource_properties={
                "TopicARN": configuration_set_topic.topic_arn
            },
            policy_statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ses:CreateConfigurationSet",
                        "ses:DeleteConfigurationSet",
                        "ses:CreateConfigurationSetEventDestination",
                        "ses:UpdateConfigurationSetEventDestination",
                        "ses:DeleteConfigurationSetEventDestination",
                    ],
                    resources=["*"],
                )
            ],
        )
