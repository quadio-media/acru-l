import json

from aws_cdk import (
    core,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_rds as rds,
)


# TODO: add option for db proxy
# https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-rds.DatabaseProxy.html
# https://docs.aws.amazon.com/cdk/api/latest/docs/aws-rds-readme.html#creating-a-database-proxy
# https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-rds.DatabaseInstanceReadReplica.html
class RDSInstance(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        db_name: str,
        db_username: str,
        vpc: ec2.Vpc,
        engine: rds.IInstanceEngine,
        allocated_storage=20,
        deletion_protection: bool = False,
        port: int = 5432,
        instance_type: ec2.InstanceType = ec2.InstanceType.of(
            ec2.InstanceClass.BURSTABLE3,
            ec2.InstanceSize.MICRO,
        ),
        removal_policy: core.RemovalPolicy = core.RemovalPolicy.DESTROY,
        multi_az: bool = False,
        storage_type: rds.StorageType = rds.StorageType.STANDARD,
        storage_encrypted: bool = True,
        backup_retention: int = 1,
        monitoring_interval: int = 60,
        enable_performance_insights: bool = True,
        cloudwatch_logs_retention: logs.RetentionDays = logs.RetentionDays.ONE_MONTH,  # noqa: E501
        auto_minor_version_upgrade: bool = True,
    ):
        super().__init__(scope, id)
        self.id = id
        self.db_name = db_name
        self.db_username = db_username

        # Creates a security group for AWS RDS
        sg_rds = ec2.SecurityGroup(
            self,
            f"{id}SecurityGroup",
            vpc=vpc,
        )

        # Adds an ingress rule which allows resources in the VPC's CIDR
        # to access the database.
        sg_rds.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(port),
        )
        self.creds = secretsmanager.Secret(
            self,
            f"{id}Credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                generate_string_key="password",
                secret_string_template=json.dumps({"username": db_username}),
            ),
        )

        self.instance = rds.DatabaseInstance(
            self,
            f"{id}Instance",
            allocated_storage=allocated_storage,
            deletion_protection=deletion_protection,
            credentials=rds.Credentials.from_password(
                username=db_username,
                password=self.creds.secret_value_from_json("password"),
            ),
            security_groups=[sg_rds],
            database_name=db_name,
            engine=engine,
            vpc=vpc,
            port=port,
            instance_type=instance_type,
            removal_policy=removal_policy,
            multi_az=multi_az,
            storage_type=storage_type,
            storage_encrypted=storage_encrypted,
            backup_retention=core.Duration.days(backup_retention),
            monitoring_interval=core.Duration.seconds(monitoring_interval),
            enable_performance_insights=enable_performance_insights,
            cloudwatch_logs_retention=cloudwatch_logs_retention,
            auto_minor_version_upgrade=auto_minor_version_upgrade,
        )

    @property
    def vpc(self) -> ec2.Vpc:
        return self.instance.vpc

    @property
    def endpoint_port(self) -> str:
        return self.instance.db_instance_endpoint_port

    @property
    def endpoint_address(self) -> str:
        return self.instance.db_instance_endpoint_address

    def setup_alarms(self):
        cloudwatch.Alarm(
            self,
            f"{self.id}HighCPU",
            metric=self.instance.metric_cpu_utilization(
                unit=cloudwatch.Unit.PERCENT
            ),
            statistic="Average",
            threshold=80,
            evaluation_periods=2,
            period=core.Duration.minutes(5),
        )

        cloudwatch.Alarm(
            self,
            f"{self.id}HighSwapSpace",
            metric=self.instance.metric(
                "SwapUsage", unit=cloudwatch.Unit.BYTES
            ),
            statistic="Average",
            threshold=209715200,  # 200MB
            evaluation_periods=2,
            period=core.Duration.minutes(5),
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        cloudwatch.Alarm(
            self,
            f"{self.id}HighReadLatency",
            metric=self.instance.metric(
                "ReadLatency", unit=cloudwatch.Unit.SECONDS
            ),
            statistic="Average",
            threshold=0.05,
            evaluation_periods=2,
            period=core.Duration.minutes(5),
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        cloudwatch.Alarm(
            self,
            f"{self.id}HighWriteLatency",
            metric=self.instance.metric(
                "WriteLatency", unit=cloudwatch.Unit.SECONDS
            ),
            statistic="Average",
            threshold=0.05,
            evaluation_periods=2,
            period=core.Duration.minutes(5),
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        cloudwatch.Alarm(
            self,
            f"{self.id}LowFreeStorage",
            metric=self.instance.metric_free_storage_space(
                unit=cloudwatch.Unit.BYTES
            ),
            threshold=1073741824,  # 1GB
            statistic="Average",
            evaluation_periods=2,
            period=core.Duration.minutes(5),
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,  # noqa: E501
        )
        cloudwatch.Alarm(
            self,
            f"{self.id}LowFreeMemory",
            metric=self.instance.metric_freeable_memory(
                unit=cloudwatch.Unit.BYTES
            ),
            threshold=104857600,  # 100MB
            evaluation_periods=2,
            period=core.Duration.minutes(5),
            statistic="Average",
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,  # noqa: E501
        )


class PostgresInstance(RDSInstance):
    def __init__(self, *args, **kwargs):
        kwargs["engine"] = rds.DatabaseInstanceEngine.POSTGRES
        super().__init__(*args, **kwargs)
