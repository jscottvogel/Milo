from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam
)
from constructs import Construct

class SchedulerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Assuming shared VPC or DB access is needed, omitting for simplicity
        # in a real setup, VPC and security groups would be configured here.

        trigger_lambda = _lambda.Function(
            self, "MiloTriggerLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("services/briefing"),
            handler="handler.lambda_handler",
            timeout=Duration.minutes(15), # LangGraph runs can take time
            memory_size=1024,
            environment={
                # To be populated via secrets manager in a real deployment
                "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/milo",
                "ANTHROPIC_API_KEY": ""
            }
        )

        # Allow SSM parameters read for integration tokens
        trigger_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=["arn:aws:ssm:*:*:parameter/milo/tenants/*/integrations/*"]
            )
        )

        # 1. Daily 7AM Morning Briefing (UTC approximation or EventBridge timezone support)
        # EventBridge supports Cron expressions
        morning_rule = events.Rule(
            self, "MorningBriefingRule",
            schedule=events.Schedule.cron(minute="0", hour="12"), # 7AM CDT approx (UTC)
        )
        morning_rule.add_target(targets.LambdaFunction(
            trigger_lambda,
            event=events.RuleTargetInput.from_object({
                "detail": {
                    "tenant_id": "all",
                    "trigger_type": "morning_briefing"
                }
            })
        ))

        # 2. Hourly Health Check
        hourly_rule = events.Rule(
            self, "HourlyHealthCheckRule",
            schedule=events.Schedule.rate(Duration.hours(1)),
        )
        hourly_rule.add_target(targets.LambdaFunction(
            trigger_lambda,
            event=events.RuleTargetInput.from_object({
                "detail": {
                    "tenant_id": "all",
                    "trigger_type": "hourly_health_check"
                }
            })
        ))

        # 3. Stale Program Daily Scan
        stale_rule = events.Rule(
            self, "StaleProgramScanRule",
            schedule=events.Schedule.cron(minute="0", hour="13"), # 8AM CDT
        )
        stale_rule.add_target(targets.LambdaFunction(
            trigger_lambda,
            event=events.RuleTargetInput.from_object({
                "detail": {
                    "tenant_id": "all",
                    "trigger_type": "stale_program_scan"
                }
            })
        ))
