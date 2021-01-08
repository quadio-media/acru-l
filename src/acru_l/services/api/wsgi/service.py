import os
from typing import List

from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_lambda_python as lambda_python,
)

from acru_l.resources.functions import PythonFunction
from acru_l.services.api.base import Service

wsgi_dirname = os.path.dirname(__file__)


class WSGIService(Service):
    def __init__(self, scope: core.Construct, id: str, *, options, **kwargs):
        if not options.api_lambda_source_path:
            options.api_lambda_source_path = os.path.join(wsgi_dirname, "src")
        kwargs["function_class"] = PythonFunction
        super().__init__(scope, id, options=options, **kwargs)

    def package_project(
        self, *, source_path: str
    ) -> List[_lambda.LayerVersion]:
        package_layer = lambda_python.PythonLayerVersion(
            self,
            "ProjectLayer",
            entry=source_path,
            compatible_runtimes=[self.runtime],
        )
        return [package_layer]
