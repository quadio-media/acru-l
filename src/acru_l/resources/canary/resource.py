import os
from aws_cdk import (
    core,
)

from acru_l.resources.custom_resources import PythonCustomResource

canary_dirname = os.path.dirname(__file__)


class Canary(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        commit_sha: str,
        version: str,
        health_check_url: str
    ):
        super().__init__(scope, id)
        self.custom_resource = PythonCustomResource(
            self,
            "CustomResource",
            source_dir=os.path.join(canary_dirname, "src"),
            index="handler.py",
            handler="main",
            resource_properties={
                "commit_sha": commit_sha,
                "version": version,
                "health_check_url": health_check_url,
            },
        )

    def add_dependency(self, resource: core.Resource):
        self.custom_resource.resource.node.add_dependency(resource)

    @property
    def resource(self):
        return self.custom_resource.resource
