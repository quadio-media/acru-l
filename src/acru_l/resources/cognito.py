import enum
from typing import cast, List, Optional, Dict

from aws_cdk import core, aws_cognito as cognito, aws_lambda as _lambda
from aws_cdk.aws_lambda_python import PythonFunction
from pydantic import BaseModel, PyObject, EmailStr


class Options(BaseModel):
    def build(self, *args, **kwargs):
        pass


def _build(conf: Optional[Options], *args, **kwargs):
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
            user_invitation=_build(options.invitation),
            user_verification=_build(options.verification),
        )

        _build(options.email_configuration, self.pool)

        self.triggers = {
            operation: fn
            for trigger in options.python_triggers
            for operation, fn in trigger.add_to_pool(
                scope=self, pool=self.pool
            )
        }


#         for
#
#         # TODO: add clients
#         # TODO: add domain
#
#
# class AppClient(Options):
#     def build(self, pool: cognito.UserPool):
#         client = pool.add_client(
#
#         )


class Operation(enum.Enum):
    CREATE_AUTH_CHALLENGE: str
    CUSTOM_MESSAGE: str
    DEFINE_AUTH_CHALLENGE: str
    POST_AUTHENTICATION: str
    POST_CONFIRMATION: str
    PRE_AUTHENTICATION: str
    PRE_SIGN_UP: str
    PRE_TOKEN_GENERATION: str
    USER_MIGRATION: str
    VERIFY_AUTH_CHALLENGE_RESPONSE: str

    @property
    def instance(self):
        return getattr(cognito.UserPoolOperation, self.value)


class PythonTrigger(Options):
    operation: Operation
    name: str
    source_path: str
    func: Optional[PyObject] = None
    runtime: Optional[PyObject] = None
    index: str = "handler.py"
    handler: str = "main"
    advanced: Dict = {}

    def add_to_pool(self, scope: core.Construct, pool: cognito.UserPool):
        func = self.func or PythonFunction
        runtime = self.runtime or _lambda.Runtime.PYTHON_3_8
        fn = func(
            scope,
            self.name,
            entry=self.source_path,
            index=self.index,
            handler=self.handler,
            runtime=runtime,
            **self.advanced,
        )
        pool.add_trigger(operation=self.operation.instance, fn=fn)
        return self.operation.instance, fn


class SignInAliases(Options):
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


class NumberConstraints(Options):
    max: int
    min: int


class StringConstraints(Options):
    max_len: int
    min_len: int


class CustomAttribute(Options):
    name: str
    data_type: str
    mutable: bool
    number_constraints: Optional[NumberConstraints] = None
    string_constraints: Optional[StringConstraints] = None

    def build(self):
        return cognito.CustomAttributeConfig(
            data_type=self.data_type,
            mutable=self.mutable,
            number_constraints=cognito.NumberAttributeConstraints(
                max=self.number_constraints.max,
                min=self.number_constraints.min,
            )
            if self.number_constraints
            else None,
            string_constraints=cognito.StringAttributeConstraints(
                max_len=self.string_constraints.max_len,
                min_len=self.string_constraints.min_len,
            )
            if self.string_constraints
            else None,
        )


class AutoVerify(Options):
    email: bool = True
    phone: bool = True

    def build(self):
        return cognito.AutoVerifiedAttrs(email=self.email, phone=self.phone)


class PasswordPolicy(Options):
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


class StandardAttribute(Options):
    mutable: Optional[bool] = None
    required: Optional[bool] = None

    def build(self):
        return cognito.StandardAttribute(
            mutable=self.mutable, required=self.required
        )


class StandardAttributes(Options):
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


class EmailSettings(Options):
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


class Invitation(Options):

    subject: Optional[str] = None
    body: Optional[str] = None
    sms: Optional[str] = None

    def build(self):
        return cognito.UserInvitationConfig(
            email_subject=self.subject,
            email_body=self.body,
            sms_message=self.sms,
        )


class Verification(Options):

    subject: Optional[str] = None
    body: Optional[str] = None
    sms: Optional[str] = None
    email_style: Optional[cognito.VerificationEmailStyle] = None

    def build(self):
        return cognito.UserVerificationConfig(
            email_subject=self.subject,
            email_body=self.body,
            sms_message=self.sms,
            email_style=self.email_style,
        )


class MFASecondFactor(Options):

    sms: Optional[bool] = None
    otp: Optional[bool] = None

    def build(self):
        return cognito.MfaSecondFactor(otp=self.otp, sms=self.sms)


class UserPoolOptions(Options):
    user_pool_name: str
    self_signup_enabled: bool = True
    sign_in_case_sensitive: bool = True
    sign_in_aliases: Optional[SignInAliases] = None
    account_recovery: cognito.AccountRecovery = (
        cognito.AccountRecovery.EMAIL_ONLY
    )
    auto_verify: AutoVerify = AutoVerify()
    mfa: Optional[cognito.Mfa] = cognito.Mfa.OFF
    mfa_second_factor: Optional[MFASecondFactor] = None

    password_policy: Optional[PasswordPolicy] = None
    standard_attributes: Optional[StandardAttributes] = None
    custom_attributes: List[CustomAttribute] = []
    email_configuration: Optional[EmailSettings] = None

    invitation: Optional[Invitation] = None
    verification: Optional[Verification] = None

    python_triggers: List[PythonTrigger] = []
