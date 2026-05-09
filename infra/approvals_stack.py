from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Duration,
)
from constructs import Construct

class ApprovalsStackConstruct(Construct):
    def __init__(
        self, scope: Construct, id: str, 
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # 1. Define the Lambda Function for the Approvals Microservice
        self.handler = _lambda.Function(
            self,
            "ApprovalsServiceHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("services/approvals"),
            handler="router.app", # Assuming router is wrapped in an app or mangum in a real deploy
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "AWS_REGION": "us-east-1",
                # "DATABASE_URL": "...", 
            }
        )

        # In a real environment, we would also grant access to the DB secret
        # and NYLAS_API_KEY from Secrets Manager here.

        # 3. Define the API Gateway
        self.api = apigw.LambdaRestApi(
            self,
            "ApprovalsApi",
            handler=self.handler,
            proxy=True,
            deploy_options=apigw.StageOptions(
                stage_name="v1"
            )
        )
