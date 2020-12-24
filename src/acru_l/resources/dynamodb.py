from typing import Optional, List

from aws_cdk import core, aws_dynamodb as ddb


class DynamoDB(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        table_name: str,
        billing_mode: ddb.BillingMode = ddb.BillingMode.PAY_PER_REQUEST,
        stream: ddb.StreamViewType = ddb.StreamViewType.NEW_AND_OLD_IMAGES,
        replication_regions: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(scope, id)
        self.table = ddb.Table(
            self,
            "Table",
            table_name=table_name,
            partition_key=ddb.Attribute(
                name="partition_key", type=ddb.AttributeType.STRING
            ),
            sort_key=ddb.Attribute(
                name="sort_key", type=ddb.AttributeType.STRING
            ),
            billing_mode=billing_mode,
            stream=stream,
            replication_regions=replication_regions,
            **kwargs
        )
