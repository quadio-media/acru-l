from aws_cdk import core
from pydantic import BaseModel

from acru_l.core import Stack, StackFactory
from acru_l.resources.cognito import UserPoolOptions, UserPool


class UsersStackOptions(BaseModel):

    user_pool: UserPoolOptions
    export_name: str


class UsersStack(Stack):
    def build(self, options: UsersStackOptions):
        user_pool = UserPool(self, "Pool", options=options.user_pool)
        core.CfnOutput(
            self,
            "UserPoolARNExport",
            value=user_pool.pool.user_pool_arn,
            export_name=options.export_name,
        )


class UsersStackFactory(StackFactory):
    stack_class = UsersStack
    options_class = UsersStackOptions
