from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnParameter,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lam,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks
)
from constructs import Construct

class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ############# CONFIGURING THE S3 BUCKET WITH TRIGGER #################
        bucket = s3.Bucket(
            self,
            "CdkBucket",
            bucket_name="cdk-simple-workflow-bucket",
            removal_policy=RemovalPolicy.DESTROY, # so it is destroyed when we delete the stack or change the name of the bucket
            auto_delete_objects=True, # same
            event_bridge_enabled=True # so we can put a trigger for the step function on the bucket

        )

        # defining the rule that triggers the step function
        trigger_rule = events.Rule(
            self,
            "CdkNewObject",
            rule_name="CdkNewObject",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                resources=[bucket.bucket_arn],
                detail_type=["Object Created"],
                detail={
                    "object": {
                        "key": [{"suffix": ".txt"}]
                    }
                }
            )
        )

        ############# CONFIGURING THE PROCESSING (PLACEHOLDER) #################
        # a simple lambda that fails / placeholder for the actual processing workload
        # code is in aws/lambda/test_failure.py
        test_failure_lambda = lam.Function(
            self,
            f"CdkFailureLambda",
            function_name=f"CdkFailureLambda",
            runtime=lam.Runtime.PYTHON_3_9,
            code=lam.Code.from_asset("lambda", exclude=["**", "!test_failure.py"]),
            handler="test_failure.lambda_handler"
        )

        ############# CONFIGURING THE ERROR NOTIFICATION #################
        # an sns topic where failures messages from lambda are posted to
        slack_topic = sns.Topic(
            self,
            "CdkFailureTopic",
            topic_name="CdkFailureTopic",
            display_name="Topic for Sfn Error Notification"
        )

        # a resource to receive the parameter passed from the command line when we cdk deploy (don't want this hard-coded here)
        email_address = CfnParameter(
            self,
            "Email",
            type="String",
            description="The Email address where error messages are sent to."
        )

        # subscribing the email to the sns topic
        slack_topic.add_subscription(
            topic_subscription=sns_subs.EmailSubscription(email_address=email_address.value_as_string)
        )

        ############# CONFIGURING THE STEP FUNCTION #################
        # predefinining what happens, when state machine reaches failure state
        publish_message = tasks.SnsPublish(
            self,
            "CdkPublishMessage",
            topic=slack_topic,
            message=sfn.TaskInput.from_json_path_at("$.Cause") # filter for cause path of the error given by the lambda
        )

        # the normal job that the state machine is supposed to do (normally a lambda that processes some data)
        submit_job = tasks.LambdaInvoke(
            self,
            "CdkSubmitJob",
            lambda_function=test_failure_lambda
        )

        # the workflow that the state machine is supposed to follow (the job can either result in success or failure and in case of failure we want to publish a notification)
        definition = (submit_job
            .add_catch(publish_message.next(sfn.Fail(self, "TaskFailed")))
        )

        # the state machine itself
        step_function = sfn.StateMachine(
            self,
            "CdkStateMachine",
            state_machine_name="CdkStateMachine",
            definition=definition,
        )
        
        # adding the trigger to the state machine so that it when an object with the .txt extension is created in the bucket
        trigger_rule.add_target(targets.SfnStateMachine(step_function))
