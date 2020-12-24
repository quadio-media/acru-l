from aws_cdk import (
    core,
    aws_apigatewayv2 as apigateway,
    aws_apigatewayv2_integrations as apigateway_integrations,
    aws_lambda as _lambda,
    aws_certificatemanager as acm,
    aws_route53 as rout53,
)


class LambdaAPIGateway(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        domain_name: str,
        certificate: acm.Certificate,
        handler: _lambda.Function,
        hosted_zone: rout53.HostedZone,
        payload_format_version: apigateway.PayloadFormatVersion = apigateway.PayloadFormatVersion.VERSION_1_0,  # noqa: E501
    ):
        super().__init__(scope, id)
        integration = apigateway_integrations.LambdaProxyIntegration(
            handler=handler, payload_format_version=payload_format_version
        )
        dn = apigateway.DomainName(
            self,
            "DomainName",
            domain_name=domain_name,
            certificate=certificate,
        )
        self.api = apigateway.HttpApi(
            self,
            "Gateway",
            default_integration=integration,
            cors_preflight=apigateway.CorsPreflightOptions(
                allow_headers=[
                    "Accept",
                    "Accept-Encoding",
                    "Authorization",
                    "Content-Type",
                    "Dnt",
                    "Origin",
                    "User-Agent",
                    "X-CSRFToken",
                    "X-Requested-With",
                ],
                allow_methods=[
                    apigateway.HttpMethod.POST,
                    apigateway.HttpMethod.GET,
                    apigateway.HttpMethod.PATCH,
                    apigateway.HttpMethod.PUT,
                    apigateway.HttpMethod.DELETE,
                    apigateway.HttpMethod.HEAD,
                    apigateway.HttpMethod.OPTIONS,
                ],
                allow_credentials=False,
                allow_origins=["*"],
                max_age=core.Duration.minutes(60),
            ),
            default_domain_mapping=apigateway.DefaultDomainMappingOptions(
                domain_name=dn,
            ),
        )

        rout53.CnameRecord(
            self,
            "Record",
            domain_name=dn.regional_domain_name,
            zone=hosted_zone,
            record_name=f"{domain_name}.",
        )
