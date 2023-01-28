#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws.aws_stack import CdkStack

app = cdk.App()
CdkStack(
    app,
    "CdkSimpleWorkflow",
    # get Aws Account and Region from environment variables so we don't have them hard-coded here
    env=cdk.Environment(
        account=os.environ["AWS_ACCOUNT"],
        region=os.environ["AWS_REGION"]
    )
)

app.synth()
