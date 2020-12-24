import boto3
import environs

from acrul_toolkit.custom_resources import CustomResourceEventHandler

env = environs.Env()

ses = boto3.client("ses")
route53 = boto3.client("route53")

CREATE = "CREATE"
UPDATE = "UPSERT"
DELETE = "DELETE"


def manage_ses_domain_validation(action):
    domain = env("DOMAIN")
    hosted_zone_id = env("HOSTED_ZONE_ID")

    verification_token = ses.verify_domain_identity(Domain=domain)[
        "VerificationToken"
    ]
    dkim_tokens = ses.verify_domain_dkim(Domain=domain)["DkimTokens"]
    print("Changing resource record sets")
    changes = [
        {
            "Action": action,
            "ResourceRecordSet": {
                "Name": f"_amazonses.{domain}.",
                "Type": "TXT",
                "TTL": 1800,
                "ResourceRecords": [{"Value": f'"{verification_token}"'}],
            },
        }
    ]
    for dkim_token in dkim_tokens:
        change = {
            "Action": action,
            "ResourceRecordSet": {
                "Name": f"{dkim_token}._domainkey.{domain}.",
                "Type": "CNAME",
                "TTL": 1800,
                "ResourceRecords": [
                    {"Value": f"{dkim_token}.dkim.amazonses.com"}
                ],
            },
        }
        changes.append(change)

    route53.change_resource_record_sets(
        ChangeBatch={"Changes": changes}, HostedZoneId=hosted_zone_id
    )


class EventHandler(CustomResourceEventHandler):
    def on_create(self, event):
        manage_ses_domain_validation(CREATE)

    def on_update(self, event):
        manage_ses_domain_validation(UPDATE)

    def on_delete(self, event):
        manage_ses_domain_validation(DELETE)


on_event = EventHandler()
