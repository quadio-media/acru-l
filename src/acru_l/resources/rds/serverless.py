import json

from aws_cdk import (
    core,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    aws_rds as rds,
)


class PostgresCluster(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        db_username: str,
        db_name: str,
        vpc: ec2.Vpc,
        stage: str = None,
        auto_pause: bool = True,
        max_capacity: int = 2,
        seconds_util_auto_pause: int = 3600,
        backup_retention_period: int = 1,
        enable_http_endpoint: bool = True,
        deletion_protection: bool = False,
    ):
        super().__init__(scope, id)

        stage = stage or ""
        name = f"{id.lower()}-{stage.lower()}" if stage else f"{id.lower()}"
        identifier = f"{name}-pg-cluster"

        self.db_name = db_name
        self.db_username = db_username

        subnet_group = rds.CfnDBSubnetGroup(
            self,
            f"{id}DBSubnetGroup",
            db_subnet_group_description="API Cluster subnets",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
        )

        self.creds = secretsmanager.Secret(
            self,
            f"{id}Credentials",
            secret_name=identifier,
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                generate_string_key="password",
                secret_string_template=json.dumps(
                    {"username": self.db_username}
                ),
            ),
        )
        db_sg = ec2.SecurityGroup(
            self, f"{id}SG", vpc=vpc, allow_all_outbound=True
        )
        db_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
        )
        sg_ids = [db_sg.security_group_id]

        self.db_cluster = rds.CfnDBCluster(
            self,
            f"{id}Cluster",
            engine="aurora-postgresql",
            engine_mode="serverless",
            engine_version="10.7",
            enable_http_endpoint=enable_http_endpoint,
            database_name=self.db_name,
            master_username=core.Fn.join(
                "",
                [
                    "{{resolve:secretsmanager:",
                    self.creds.secret_arn,
                    ":SecretString:username}}",
                ],
            ),
            master_user_password=core.Fn.join(
                "",
                [
                    "{{resolve:secretsmanager:",
                    self.creds.secret_arn,
                    ":SecretString:password}}",
                ],
            ),
            backup_retention_period=backup_retention_period,
            scaling_configuration={
                "auto_pause": auto_pause,
                "max_capacity": max_capacity,
                "min_capacity": 2,
                "seconds_util_auto_pause": seconds_util_auto_pause,
            },
            vpc_security_group_ids=sg_ids,
            db_subnet_group_name=subnet_group.ref,
            deletion_protection=deletion_protection,
        )
        self.db_cluster_arn = f"arn:aws:rds:{scope.region}:{scope.account}:cluster:{self.db_cluster.ref}"  # noqa: E501

    @property
    def endpoint_port(self):
        return self.db_cluster.attr_endpoint_port

    @property
    def endpoint_address(self):
        return self.db_cluster.attr_endpoint_address
