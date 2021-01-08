import json

from aws_cdk import (
    core,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_rds as rds,
)
from pydantic import BaseModel


class RDSInstanceOptions(BaseModel):
    db_name: str
    db_username: str
    add_proxy: bool = False
    multi_az: bool = False
    deletion_protection: bool = False
    setup_alarms: bool = False
    instance_class: str = "BURSTABLE3"
    instance_size: str = "MICRO"

    allocated_storage: int = 20
    port: int = 5432
    removal_policy: core.RemovalPolicy = core.RemovalPolicy.DESTROY
    storage_type: rds.StorageType = rds.StorageType.STANDARD
    storage_encrypted: bool = True
    backup_retention: int = 1
    monitoring_interval: int = 60
    enable_performance_insights: bool = True
    cloudwatch_logs_retention: logs.RetentionDays = (
        logs.RetentionDays.ONE_MONTH
    )  # noqa: E501
    auto_minor_version_upgrade: bool = True

    @property
    def instance_type(self) -> ec2.InstanceType:
        return ec2.InstanceType.of(
            getattr(ec2.InstanceClass, self.instance_class),
            getattr(ec2.InstanceSize, self.instance_size),
        )


class RDSInstance(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        vpc: ec2.Vpc,
        engine: rds.IInstanceEngine,
        options: RDSInstanceOptions,
    ):
        super().__init__(scope, id)
        self.id = id
        self.db_name = options.db_name
        self.db_username = options.db_username

        # Creates a security group for AWS RDS
        sg_rds = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
        )

        # Adds an ingress rule which allows resources in the VPC's CIDR
        # to access the database.
        sg_rds.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(options.port),
        )
        self.creds = secretsmanager.Secret(
            self,
            "Credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                generate_string_key="password",
                secret_string_template=json.dumps(
                    {"username": options.db_username}
                ),
            ),
        )

        self.instance = rds.DatabaseInstance(
            self,
            "Instance",
            allocated_storage=options.allocated_storage,
            deletion_protection=options.deletion_protection,
            credentials=rds.Credentials.from_password(
                username=options.db_username,
                password=self.creds.secret_value_from_json("password"),
            ),
            security_groups=[sg_rds],
            database_name=options.db_name,
            engine=engine,
            vpc=vpc,
            port=options.port,
            instance_type=options.instance_type,
            removal_policy=options.removal_policy,
            multi_az=options.multi_az,
            storage_type=options.storage_type,
            storage_encrypted=options.storage_encrypted,
            backup_retention=core.Duration.days(options.backup_retention),
            monitoring_interval=core.Duration.seconds(
                options.monitoring_interval
            ),
            enable_performance_insights=options.enable_performance_insights,
            cloudwatch_logs_retention=options.cloudwatch_logs_retention,
            auto_minor_version_upgrade=options.auto_minor_version_upgrade,
        )
        self.port = options.port
        self.proxy = None
        if options.add_proxy:
            self.proxy = self.instance.add_proxy(
                "Proxy",
                secrets=[self.creds],
                vpc=vpc,
                db_proxy_name=f"{scope.stack_name}-{id}-Proxy",
                security_groups=[sg_rds],
            )
        if options.setup_alarms:
            self.setup_alarms()

    @property
    def connection_interface(self):
        return self.proxy or self.instance

    @property
    def vpc(self) -> ec2.Vpc:
        return self.instance.vpc

    @property
    def endpoint_port(self) -> str:
        return self.instance.db_instance_endpoint_port

    @property
    def endpoint_address(self) -> str:
        if self.proxy:
            return self.proxy.endpoint
        return self.instance.db_instance_endpoint_address

    def setup_alarms(self):
        cloudwatch.Alarm(
            self,
            "HighCPU",
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
            "HighSwapSpace",
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
            "HighReadLatency",
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
            "HighWriteLatency",
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
            "LowFreeStorage",
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
            "LowFreeMemory",
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
        kwargs["engine"] = rds.DatabaseInstanceEngine.postgres(
            version=rds.PostgresEngineVersion.VER_11_5
        )
        super().__init__(*args, **kwargs)
