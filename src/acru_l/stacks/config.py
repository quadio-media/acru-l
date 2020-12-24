from typing import Optional, Mapping, Any, TypeVar, List

from pydantic import BaseModel, Extra
from aws_cdk import core, aws_ec2 as ec2, aws_secretsmanager as secretsmanager


class VpcConfig(BaseModel):
    cidr: str
    export_name: str


class HostedZoneConfig(BaseModel):
    domain_name: str
    export_name: str
    use_github_pages: bool = False


class NetworkConfig(BaseModel):
    vpc: VpcConfig
    hosted_zone: HostedZoneConfig


class SecretsConfig(BaseModel):
    name: str
    arn_key: str
    exclude_punctuation: bool = True
    include_space: bool = False
    password_length: int = 32

    class Config:
        extra = Extra.allow

    def create(self, *, scope: core.Construct) -> secretsmanager.Secret:
        return secretsmanager.Secret(
            scope,
            self.name,
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=self.exclude_punctuation,
                include_space=self.include_space,
                password_length=self.password_length,
            ),
        )


class CanaryConfig(BaseModel):

    commit_sha: str
    version: str
    health_check_url: str

    class Config:
        extra = Extra.allow


class CustomResourceConfig(BaseModel):

    source_path: str
    properties: Mapping[str, Any]

    class Config:
        extra = Extra.allow


class ServiceConfig(BaseModel):
    domain_name: str
    project_source_path: str
    secrets: Optional[List[SecretsConfig]]
    environment: Optional[Mapping[str, Any]]
    health_check_url: Optional[str] = None
    pre_deploy_config: Optional[CustomResourceConfig] = None
    post_deploy_config: Optional[CustomResourceConfig] = None

    class Config:
        extra = Extra.allow


class RDSConfig(BaseModel):
    db_name: str
    db_username: str
    multi_az: bool = False
    deletion_protection: bool = False
    setup_alarms: bool = False
    instance_class: str = "BURSTABLE3"
    instance_size: str = "MICRO"

    class Config:
        extra = Extra.allow

    @property
    def instance_type(self) -> ec2.InstanceType:
        return ec2.InstanceType.of(
            getattr(ec2.InstanceClass, self.instance_class),
            getattr(ec2.InstanceSize, self.instance_size),
        )


class APIConfig(BaseModel):
    hosted_zone_domain_name: str
    cert_export_name: str
    version: str
    vpc_name: str
    rds_config: Optional[RDSConfig]
    service_config: Optional[ServiceConfig]

    class Config:
        extra = Extra.allow


class CertConfig(BaseModel):
    domain_name: str
    export_prefix: str = ""
    subdomains: Optional[List[str]] = None

    class Config:
        extra = Extra.allow


DataModelT = TypeVar("DataModelT")
