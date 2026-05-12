"""Hourly Monitor Stack — AWS CDK Python.

Defines the EventBridge Scheduler rule and Lambda function for the
Hourly Autonomous Program Monitor. This stack is SEPARATE from the
daily briefing stack (infra/scheduler_stack.py).

Do NOT merge this stack with the briefing scheduler stack.
Do NOT add daily briefing resources to this stack.
Do NOT reference the daily briefing Lambda or its EventBridge rule here.

Deployment (PoC mode):
    cdk deploy HourlyMonitorStack -c mode=poc
"""
from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_logs as logs
from constructs import Construct


class HourlyMonitorStack(cdk.Stack):
    """CloudFormation stack for the Hourly Program Monitor Lambda + EventBridge rule.

    This stack provisions:
    - A dedicated IAM execution role with permissions for CloudWatch Logs,
      Lambda invocation, and SES email sending.
    - A Lambda function that runs apps/api/hourly_monitor_handler.py.
    - An EventBridge rule firing every 60 minutes, independent of the daily
      briefing EventBridge rule.
    - A CloudWatch Log Group with 7-day retention.

    Args:
        scope: CDK construct scope.
        construct_id: Stack logical ID.
        mode: 'poc' or 'prod'. In 'poc' mode, reserved concurrency is capped at 2.
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
            "HourlyMonitorLogGroup",
            log_group_name="/milo/hourly-monitor",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY if is_poc else cdk.RemovalPolicy.RETAIN,
        )

        # -----------------------------------------------------------------------
        # IAM Execution Role — dedicated to the hourly monitor Lambda only.
        # Separate from the daily briefing Lambda role.
        # -----------------------------------------------------------------------
        execution_role = iam.Role(
            self,
            "HourlyMonitorLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description=(
                "Execution role for milo-hourly-monitor Lambda. "
                "Separate from the daily briefing Lambda role."
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # CloudWatch Logs — write logs from the Lambda function
        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogs",
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    log_group.log_group_arn,
                    f"{log_group.log_group_arn}:*",
                ],
            )
        )

        # CloudWatch Metrics — emit custom metrics
        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchMetrics",
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        # Lambda — invoke other Lambda functions (e.g. implement_feature MCP tool)
        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="LambdaInvoke",
                actions=[
                    "lambda:InvokeFunction",
                    "lambda:InvokeAsync",
                ],
                resources=[
                    f"arn:aws:lambda:{self.region}:{self.account}:function:milo-*",
                ],
            )
        )

        # SES — send handoff emails
        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="SESEmailSend",
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail",
                ],
                resources=["*"],
            )
        )

        # Bedrock — invoke models for the agent runtime
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

        # Secrets Manager — read DATABASE_URL and integration secrets
        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="SecretsRead",
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:milo/*"
                ],
            )
        )

        # SSM Parameter Store — read OAuth tokens and tenant config
        execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="ParameterStoreRead",
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/milo/*"
                ],
            )
        )

        # S3 — read/write tenant-scoped prefix for engineering_requests/ and storage
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
        # Lambda Function — hourly monitor only.
        # Handler: hourly_monitor_handler.lambda_handler
        # Entry point is apps/api/hourly_monitor_handler.py, NOT the daily briefing.
        # -----------------------------------------------------------------------
        fn = lambda_.DockerImageFunction(
            self,
            "HourlyMonitorFunction",
            function_name="milo-hourly-monitor",
            code=lambda_.DockerImageCode.from_image_asset(
                "apps/api",
                cmd=["hourly_monitor_handler.lambda_handler"],
            ),
            role=execution_role,
            memory_size=1024,
            timeout=cdk.Duration.minutes(14),  # under the 15-min Lambda hard limit
            reserved_concurrent_executions=2 if is_poc else 10,
            log_group=log_group,
            environment={
                "LOG_LEVEL": "INFO",
                # MILO_REPO_PATH: filesystem path used by the implement_feature MCP tool.
                # In Lambda this should point to an EFS mount or a bundled snapshot.
                "MILO_REPO_PATH": "/mnt/repo",
                # DATABASE_URL is injected at deploy time via Secrets Manager or
                # a CDK environment variable substitution; set it in the deployment
                # pipeline rather than hardcoding here.
            },
            description=(
                "Hourly Autonomous Program Monitor — runs every 60 minutes. "
                "Completely separate from the daily morning briefing Lambda."
            ),
        )

        # -----------------------------------------------------------------------
        # EventBridge Rule — rate(1 hour).
        # This rule is INDEPENDENT of the daily briefing EventBridge rule
        # defined in infra/scheduler_stack.py.  The two rules must never be
        # merged or share targets.
        # -----------------------------------------------------------------------
        rule = events.Rule(
            self,
            "HourlyMonitorRule",
            rule_name="milo-hourly-monitor-rule",
            description=(
                "Triggers milo-hourly-monitor Lambda every 60 minutes. "
                "Independent of the daily morning briefing EventBridge rule."
            ),
            schedule=events.Schedule.rate(cdk.Duration.hours(1)),
            enabled=True,
        )
        rule.add_target(targets.LambdaFunction(fn))

        # -----------------------------------------------------------------------
        # CloudFormation Outputs
        # -----------------------------------------------------------------------
        cdk.CfnOutput(
            self,
            "HourlyMonitorFunctionArn",
            value=fn.function_arn,
            description="ARN of the Hourly Monitor Lambda function.",
            export_name="milo-hourly-monitor-fn-arn",
        )
        cdk.CfnOutput(
            self,
            "HourlyMonitorRuleArn",
            value=rule.rule_arn,
            description="ARN of the EventBridge rule that triggers the Hourly Monitor.",
            export_name="milo-hourly-monitor-rule-arn",
        )
        cdk.CfnOutput(
            self,
            "HourlyMonitorLogGroupName",
            value=log_group.log_group_name,
            description="CloudWatch Log Group for the Hourly Monitor Lambda.",
            export_name="milo-hourly-monitor-log-group",
        )
