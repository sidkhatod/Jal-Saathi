from aws_cdk import (
    Stack,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct

class RolesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, 
                 photos_bucket, datasets_bucket, 
                 farms_table, plots_table, observations_table, advisories_table, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.lambda_role = iam.Role(
            self, "JalSaathiLambdaExecutionRole",
            role_name=f"JalSaathiLambdaExecutionRole-{env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        # CloudWatch Logs (using AWS Managed Policy for basic execution)
        self.lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        # S3 Read/Write
        photos_bucket.grant_read_write(self.lambda_role)
        datasets_bucket.grant_read_write(self.lambda_role)

        # DynamoDB Read/Write
        farms_table.grant_read_write_data(self.lambda_role)
        plots_table.grant_read_write_data(self.lambda_role)
        observations_table.grant_read_write_data(self.lambda_role)
        advisories_table.grant_read_write_data(self.lambda_role)

        # Bedrock
        # Note: We scope to all foundation models in the region because exact model ARNs vary.
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[f"arn:aws:bedrock:{self.region}::foundation-model/*"]
        ))

        # Transcribe
        # Note: Most transcribe actions (like StartTranscriptionJob) don't support resource-level scoping on job creation
        # unless you restrict by specific predetermined job names, which are usually dynamic.
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "transcribe:StartTranscriptionJob",
                "transcribe:GetTranscriptionJob"
            ],
            resources=["*"]
        ))

        # Polly
        # Note: SynthesizeSpeech does not support resource-level permissions in IAM (must be '*').
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["polly:SynthesizeSpeech"],
            resources=["*"]
        ))

        # Translate
        # Note: TranslateText does not support resource-level permissions in IAM (must be '*').
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["translate:TranslateText"],
            resources=["*"]
        ))

        # Amazon Location Service
        # Note: We scope to all place indexes in the account/region since we don't have a specific index ARN yet.
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "geo:SearchPlaceIndexForPosition",
                "geo:SearchPlaceIndexForText"
            ],
            resources=[f"arn:aws:geo:{self.region}:{self.account}:place-index/*"]
        ))

        # Output the Role ARN
        CfnOutput(
            self, "LambdaRoleArn",
            value=self.lambda_role.role_arn,
            description="ARN of the Jal-Saathi Lambda Execution Role"
        )
