"""Daily Briefing Scheduler Stack — AWS CDK Python.

This stack provisions ONLY the daily morning briefing Lambda and its
EventBridge rule. It is SEPARATE from the Hourly Program Monitor stack
(infra/hourly_monitor_stack.py).

Do NOT add hourly monitor resources to this stack.
Do NOT merge with HourlyMonitorStack.
"""
from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_logs as logs
from constructs import Construct


class SchedulerStack(cdk.Stack):
    """CloudFormation stack for the Daily Morning Briefing Lambda + EventBridge rule.

    This stack provisions:
    - A dedicated IAM execution role for the briefing Lambda.
    - A Lambda function that runs apps/api/briefing_handler.py.
    - An EventBridge rule firing every day at 07:00 UTC.
    - A CloudWatch Log Group with 7-day retention.

    Args:
        scope: CDK construct scope.
        construct_id: Stack logical ID.
        mode: 'poc' or 'prod'.
        **kwargs: Passed to cdk.Stack.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        mode: str = "poc",
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)  # type: ignore[arg-type]

        is_poc = mode == "poc"

        # -----------------------------------------------------------------------
        # CloudWatch Log Group
        # -----------------------------------------------------------------------
        log_group = logs.LogGroup(
            self,
            "BriefingLogGroup",
            log_group_name="/milo/morning-briefing",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY if is_poc else cdk.RemovalPolicy.RETAIN,
        )

        # -----------------------------------------------------------------------
        # IAM Execution Role — separate from the hourly monitor Lambda role
        # -----------------------------------------------------------------------
        execution_role = iam.Role(
            self,
            "BriefingLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for milo-morning-briefing Lambda. Separate from hourly monitor Lambda role.",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockInvoke",
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["arn:aws:bedrock:*::foundation-model/*"],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="SecretsRead",
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:milo/*"
                ],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="ParameterStoreRead",
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/milo/*"
                ],
            )
        )

        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3TenantAccess",
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket",
                ],
                resources=[
                    f"arn:aws:s3:::milo-tenants-{self.account}",
                    f"arn:aws:s3:::milo-tenants-{self.account}/*",
                ],
            )
        )

        # -----------------------------------------------------------------------
        # Lambda Function — daily briefing only
        # -----------------------------------------------------------------------
        fn = lambda_.DockerImageFunction(
            self,
            "BriefingFunction",
            function_name="milo-morning-briefing",
            code=lambda_.DockerImageCode.from_image_asset(
                "apps/api",
                cmd=["briefing_handler.handler"],
            ),
            role=execution_role,
            memory_size=1024,
            timeout=cdk.Duration.minutes(14),
            reserved_concurrent_executions=2 if is_poc else 10,
            log_group=log_group,
            environment={
                "LOG_LEVEL": "INFO",
            },
            description="Daily Morning Briefing Lambda — separate from Hourly Monitor Lambda.",
        )

        #