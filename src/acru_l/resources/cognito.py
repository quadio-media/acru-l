import enum
import os
from typing import cast, List, Optional, Union, Mapping, Dict

from aws_cdk import (
    core,
    aws_certificatemanager as acm,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
)
from aws_cdk.aws_lambda_python import PythonFunction, PythonLayerVersion
from pydantic import (
    BaseModel,
    PyObject,
    EmailStr,
    Field,
    FilePath,
    DirectoryPath,
)


class Factory(BaseModel):
    def build(self, *args, **kwargs):
        pass


def _build(conf: Optional[Factory], *args, **kwargs):
    if not conf:
        return
    return conf.build(*args, **kwargs)


class UserPool(core.Construct):
    def __init__(
        self, scope: core.Construct, id: str, *, options: "UserPoolOptions"
    ):
        super().__init__(scope, id)

        self.pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=options.user_pool_name,
            account_recovery=options.account_recovery,
            auto_verify=_build(options.auto_verify),
            custom_attributes={
                attr.name: attr.build() for attr in options.custom_attributes
            },
            mfa=options.mfa,
            mfa_second_factor=_build(options.mfa_second_factor),
            password_policy=_build(options.password_policy),
            self_sign_up_enabled=options.self_signup_enabled,
            sign_in_aliases=_build(options.sign_in_aliases),
            sign_in_case_sensitive=options.sign_in_case_sensitive,
            standard_attributes=_build(options.standard_attributes),
            user_invitation=_build(options.invitation_options),
            user_verification=_build(options.verification_options),
        )

        _build(options.email_configuration, self.pool)

        self.triggers = {}

        for trigger in options.python_triggers:
            operation, fn = trigger.build(scope=self, pool=self.pool)
            self.triggers[operation] = fn

        for app_client in options.app_clients:
            app_client.build(self, self.pool)

        if options.app_clients:
            _build(options.domain_options, self, self.pool)


class AppClientFactory(Factory):

    name: str
    export_name: str
    admin_user_password: Optional[bool] = None
    user_password: Optional[bool] = None
    user_srp: Optional[bool] = None
    prevent_user_existence_errors: Optional[bool] = None

    def build(self, scope: core.Construct, pool: cognito.UserPool):
        client = pool.add_client(
            self.name,
            auth_flows=cognito.AuthFlow(
                admin_user_password=self.admin_user_password,
                user_srp=self.user_srp,
                user_password=self.user_password,
            ),
            prevent_user_existence_errors=self.prevent_user_existence_errors,
        )
        core.CfnOutput(
            scope,
            self.export_name,
            value=client.user_pool_client_id,
            export_name=self.export_name,
        )


class Operation(enum.Enum):
    CREATE_AUTH_CHALLENGE: str = "CREATE_AUTH_CHALLENGE"
    CUSTOM_MESSAGE: str = "CUSTOM_MESSAGE"
    DEFINE_AUTH_CHALLENGE: str = "DEFINE_AUTH_CHALLENGE"
    POST_AUTHENTICATION: str = "POST_AUTHENTICATION"
    POST_CONFIRMATION: str = "POST_CONFIRMATION"
    PRE_AUTHENTICATION: str = "PRE_AUTHENTICATION"
    PRE_SIGN_UP: str = "PRE_SIGN_UP"
    PRE_TOKEN_GENERATION: str = "PRE_TOKEN_GENERATION"
    USER_MIGRATION: str = "USER_MIGRATION"
    VERIFY_AUTH_CHALLENGE_RESPONSE: str = "VERIFY_AUTH_CHALLENGE_RESPONSE"

    @property
    def instance(self):
        return getattr(cognito.UserPoolOperation, self.value)


class PythonFunctionLayerFactory(Factory):
    name: str
    arn_export_name: Optional[str] = None
    source_path: Optional[DirectoryPath] = None

    def build(self, scope: core.Construct, runtime: _lambda.Runtime):
        if self.arn_export_name:
            arn = core.Fn.import_value(self.arn_export_name)
            return PythonLayerVersion.from_layer_version_arn(
                scope, self.name, layer_version_arn=arn
            )
        return PythonLayerVersion(
            scope,
            self.name,
            entry=str(self.source_path),
            compatible_runtimes=[runtime],
        )


class PythonFunctionFactory(Factory):
    name: str
    source_path: DirectoryPath
    export_name: str

    runtime: Optional[PyObject] = None
    index: str = "handler.py"
    handler: str = "main"
    memory_size: int = 512
    profiling: bool = True
    tracing: Optional[_lambda.Tracing] = None
    layers: List[PythonFunctionLayerFactory] = Field(default_factory=list)
    description: Optional[str] = None
    environment: Optional[Dict[str, str]] = Field(default_factory=dict)
    local_environment_names: List[str] = Field(default_factory=list)
    log_retention: logs.RetentionDays = logs.RetentionDays.ONE_DAY
    pool_actions: List[str] = Field(default_factory=list)
    retry_attempts: int = 2

    def build(self, scope: core.Construct, pool: cognito.UserPool):
        runtime = self.runtime or _lambda.Runtime.PYTHON_3_8
        layers = [opts.build(scope, runtime) for opts in self.layers]
        for name in self.local_environment_names:
            self.environment[name] = os.environ[name]
        fn = PythonFunction(
            scope,
            self.name,
            runtime=runtime,
            entry=str(self.source_path),
            index=self.index,
            handler=self.handler,
            layers=layers,
            description=self.description,
            environment=self.environment,
            log_retention=self.log_retention,
            profiling=self.profiling,
            memory_size=self.memory_size,
            tracing=self.tracing,
        )
        if self.pool_actions:
            policy = iam.Policy(
                scope,
                f"{self.name}PoolPolicy",
                statements=[
                    iam.PolicyStatement(
                        actions=self.pool_actions,
                        resources=[pool.user_pool_arn],
                    )
                ],
            )
            fn.role.attach_inline_policy(policy)

        core.CfnOutput(
            scope,
            f"{self.name}Output",
            value=fn.function_arn,
            export_name=self.export_name,
            description=self.description,
        )
        return fn


class PythonTriggerFactory(Factory):
    operation: Operation
    function_options: PythonFunctionFactory

    def build(self, scope: core.Construct, pool: cognito.UserPool):
        fn = self.function_options.build(scope, pool)
        pool.add_trigger(operation=self.operation.instance, fn=fn)
        return self.operation, fn


class SignInAliases(Factory):
    email: Optional[bool] = None
    phone: Optional[bool] = None
    preferred_username: Optional[bool] = None
    username: Optional[bool] = None

    def build(self):
        return cognito.SignInAliases(
            email=self.email,
            phone=self.phone,
            preferred_username=self.preferred_username,
            username=self.username,
        )


class CustomAttribute(Factory):
    name: str
    attr_class: PyObject
    mutable: bool = False
    extra: Optional[Mapping[str, Union[float, int]]] = Field(
        default_factory=dict
    )

    def build(self):
        return self.attr_class(mutable=self.mutable, **self.extra)


class AutoVerify(Factory):
    email: bool = True
    phone: bool = True

    def build(self):
        return cognito.AutoVerifiedAttrs(email=self.email, phone=self.phone)


class PasswordPolicy(Factory):
    min_length: Optional[int] = None
    require_digits: Optional[bool] = None
    require_lowercase: Optional[bool] = None
    require_symbols: Optional[bool] = None
    require_uppercase: Optional[bool] = None
    temp_password_validity: Optional[int] = None

    def build(self):
        return cognito.PasswordPolicy(
            min_length=self.min_length,
            require_digits=self.require_digits,
            require_lowercase=self.require_lowercase,
            require_symbols=self.require_symbols,
            require_uppercase=self.require_uppercase,
            temp_password_validity=core.Duration.days(
                self.temp_password_validity
            )
            if self.temp_password_validity
            else None,
        )


class StandardAttribute(Factory):
    mutable: Optional[bool] = None
    required: Optional[bool] = None

    def build(self):
        return cognito.StandardAttribute(
            mutable=self.mutable, required=self.required
        )


class StandardAttributes(Factory):
    address: Optional[StandardAttribute] = None
    birthdate: Optional[StandardAttribute] = None
    email: Optional[StandardAttribute] = None
    family_name: Optional[StandardAttribute] = None
    fullname: Optional[StandardAttribute] = None
    gender: Optional[StandardAttribute] = None
    given_name: Optional[StandardAttribute] = None
    last_update_time: Optional[StandardAttribute] = None
    locale: Optional[StandardAttribute] = None
    middle_name: Optional[StandardAttribute] = None
    nickname: Optional[StandardAttribute] = None
    phone_number: Optional[StandardAttribute] = None
    preferred_username: Optional[StandardAttribute] = None
    profile_page: Optional[StandardAttribute] = None
    profile_picture: Optional[StandardAttribute] = None
    timezone: Optional[StandardAttribute] = None
    website: Optional[StandardAttribute] = None

    def build(self):
        return cognito.StandardAttributes(
            address=_build(self.address),
            birthdate=_build(self.birthdate),
            email=_build(self.email),
            family_name=_build(self.family_name),
            fullname=_build(self.fullname),
            gender=_build(self.gender),
            given_name=_build(self.given_name),
            last_update_time=_build(self.last_update_time),
            locale=_build(self.locale),
            middle_name=_build(self.middle_name),
            nickname=_build(self.nickname),
            phone_number=_build(self.phone_number),
            preferred_username=_build(self.preferred_username),
            profile_page=_build(self.profile_page),
            profile_picture=_build(self.profile_picture),
            timezone=_build(self.timezone),
            website=_build(self.website),
        )


class EmailSettings(Factory):
    source_arn: Optional[str] = None
    from_: Optional[str] = None
    from_email: Optional[EmailStr] = None
    reply_to_email_address: Optional[str] = None
    email_sending_account: Optional[str] = None
    configuration_set: Optional[str] = None

    def build(self, pool: cognito.UserPool):
        region = pool.stack.region
        account = pool.stack.account
        email = self.from_email
        if email:
            source_arn = f"arn:aws:ses:{region}:{account}:identity/{email}"
            from_ = None
            email_sending_account = "DEVELOPER"
        else:
            source_arn = self.source_arn
            from_ = self.from_
            email_sending_account = self.email_sending_account

        conf = cognito.CfnUserPool.EmailConfigurationProperty(
            source_arn=source_arn,
            from_=from_,
            reply_to_email_address=self.reply_to_email_address,
            email_sending_account=email_sending_account,
            configuration_set=self.configuration_set,
        )
        cfn_pool = cast(cognito.CfnUserPool, pool.node.default_child)
        cfn_pool.email_configuration = conf
        return conf


class InvitationFactory(Factory):

    subject: Optional[FilePath] = None
    body: Optional[FilePath] = None
    sms: Optional[FilePath] = None

    def build(self):
        return cognito.UserInvitationConfig(
            email_subject=self.subject.read_text(),
            email_body=self.body.read_text(),
            sms_message=self.sms.read_text(),
        )


class VerificationFactory(Factory):

    subject: Optional[FilePath] = None
    body: Optional[FilePath] = None
    sms: Optional[FilePath] = None
    email_style: Optional[cognito.VerificationEmailStyle] = None

    def build(self):
        return cognito.UserVerificationConfig(
            email_subject=self.subject.read_text(),
            email_body=self.body.read_text(),
            sms_message=self.sms.read_text(),
            email_style=self.email_style,
        )


class MFASecondFactorFactory(Factory):

    sms: Optional[bool] = None
    otp: Optional[bool] = None

    def build(self):
        return cognito.MfaSecondFactor(otp=self.otp, sms=self.sms)


class DomainFactory(Factory):
    name: str
    domain_name: str
    cert_export_name: str

    def build(self, scope: core.Construct, pool: cognito.UserPool):
        certificate = acm.Certificate.from_certificate_arn(
            scope,
            "Certificate",
            core.Fn.import_value(self.cert_export_name),
        )
        pool.add_domain(
            self.name,
            custom_domain=cognito.CustomDomainOptions(
                domain_name=self.domain_name, certificate=certificate
            ),
        )


class UserPoolOptions(BaseModel):
    user_pool_name: str
    self_signup_enabled: bool = True
    sign_in_case_sensitive: bool = True
    sign_in_aliases: Optional[SignInAliases] = None
    account_recovery: cognito.AccountRecovery = (
        cognito.AccountRecovery.EMAIL_ONLY
    )
    auto_verify: AutoVerify = AutoVerify()
    mfa: Optional[cognito.Mfa] = cognito.Mfa.OFF
    mfa_second_factor: Optional[MFASecondFactorFactory] = None

    password_policy: Optional[PasswordPolicy] = None
    standard_attributes: Optional[StandardAttributes] = None
    custom_attributes: List[CustomAttribute] = Field(default_factory=list)
    email_configuration: Optional[EmailSettings] = None

    invitation_options: Optional[InvitationFactory] = None
    verification_options: Optional[VerificationFactory] = None

    python_triggers: List[PythonTriggerFactory] = Field(default_factory=list)

    app_clients: List[AppClientFactory] = Field(default_factory=list)
    domain_options: Optional[DomainFactory] = None
