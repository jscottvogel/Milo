#!/usr/bin/env python3
import os
import sys
import aws_cdk as cdk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infra.hourly_monitor_stack import HourlyMonitorStack

app = cdk.App()
HourlyMonitorStack(
    app,
    "MiloHourlyMonitorStack",
    mode="poc",  # or "prod", based on your environment
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT") or os.environ.get("AWS_ACCOUNT_ID") or "520477993393",
        region=os.environ.get("CDK_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
    )
)
app.synth()
