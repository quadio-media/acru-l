import boto3
import time

from acrul_toolkit.custom_resources import CustomResourceEventHandler

ses = boto3.client("ses")


def verify_emails(email_addresses=None):
    email_addresses = email_addresses or []
    for email_address in email_addresses:
        ses.verify_email_identity(EmailAddress=email_address)
        time.sleep(1)


class EventHandler(CustomResourceEventHandler):
    @staticmethod
    def get_emails(event):
        return event["ResourceProperties"]["emails"]

    def on_create(self, event):
        verify_emails(self.get_emails(event))

    def on_update(self, event):
        verify_emails(self.get_emails(event))

    def on_delete(self, event):
        pass


on_event = EventHandler()
