# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html
import boto3
import environs

from acrul_toolkit.custom_resources import CustomResourceEventHandler


env = environs.Env()


class EventHandler(CustomResourceEventHandler):

    configuration_set_name = env("CONFIGURATION_SET_NAME")
    event_destination_name = env("EVENT_DESTINATION_NAME")

    def __init__(self):
        self.client = boto3.client("ses")

    def on_create(self, event):
        self.create_configuration_set(event)
        self.create_event_destination(event)

    def on_update(self, event):
        self.update_event_destination(event)

    def on_delete(self, event):
        self.delete_event_destination(event)
        self.delete_configuration_set(event)

    @staticmethod
    def get_topic_arn(event):
        return event["ResourceProperties"]["TopicARN"]

    def create_configuration_set(self, event):
        return self.client.create_configuration_set(
            ConfigurationSet={"Name": self.configuration_set_name}
        )

    def delete_configuration_set(self, event):
        return self.client.delete_configuration_set(
            ConfigurationSetName=self.configuration_set_name
        )

    def create_event_destination(self, event):
        return self.client.create_configuration_set_event_destination(
            **self.get_destination_config(event)
        )

    def update_event_destination(self, event):
        return self.client.update_configuration_set_event_destination(
            **self.get_destination_config(event)
        )

    def delete_event_destination(self, event):
        return self.client.delete_configuration_set_event_destination(
            ConfigurationSetName=self.configuration_set_name,
            EventDestinationName=self.event_destination_name,
        )

    def get_destination_config(self, event):
        return dict(
            ConfigurationSetName=self.configuration_set_name,
            EventDestination={
                "Name": self.event_destination_name,
                "Enabled": True,
                "MatchingEventTypes": [
                    "send",
                    "reject",
                    "bounce",
                    "complaint",
                    "delivery",
                    "open",
                    "click",
                    "renderingFailure",
                ],
                "SNSDestination": {"TopicARN": self.get_topic_arn(event)},
            },
        )


main = EventHandler()
