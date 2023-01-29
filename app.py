#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Tags
from aws.aws_stack import CdkStack

app = App()
stack = CdkStack(
    app,
    "CdkSimpleWorkflow",
    # get Aws Account and Region from environment variables so we don't have them hard-coded here
    env=Environment(
        account=os.environ["AWS_ACCOUNT"],
        region=os.environ["AWS_REGION"]
    )
)

Tags.of(stack).add("IaC", "cdk")
Tags.of(stack).add("Project", "cdk-simple-sfn")

app.synth()
