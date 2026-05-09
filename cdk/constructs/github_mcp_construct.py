from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Duration,
)
from constructs import Construct

class GitHubMcpConstruct(Construct):
    def __init__(
        self, scope: Construct, id: str, 
        secret_name: str = "milo/github/token", 
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # 1. Reference the Secrets Manager secret
        github_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GitHubTokenSecret", secret_name
        )

        # 2. Define the Lambda Function
        # Assuming containerized Lambda or standard python runtime based on workspace patterns
        # Here we use standard PythonFunction for simplicity or you can swap to DockerImageFunction
        self.handler = _lambda.Function(
            self,
            "GitHubMcpHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("services/mcp/github"),
            handler="main.app", # Assuming a handler wrapper or Mangum is used in a real deploy, but this matches requested standard
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "AWS_REGION": "us-east-1"
            }
        )

        # Grant Lambda permissions to read the secret
        github_secret.grant_read(self.handler)

        # 3. Define the API Gateway
        self.api = apigw.LambdaRestApi(
            self,
            "GitHubMcpApi",
            handler=self.handler,
            proxy=True,
            deploy_options=apigw.StageOptions(
                stage_name="v1"
            )
        )
