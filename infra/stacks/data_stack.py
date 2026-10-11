from aws_cdk import (
    Stack,
    aws_s3 as s3,
    RemovalPolicy,
    Duration,
    Tags
)
from constructs import Construct

class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Photos Bucket
        self.photos_bucket = s3.Bucket(
            self, "PhotosBucket",
            bucket_name=f"jal-saathi-photos-{env_name}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN, # Retain by default to prevent data loss
        )

        self.photos_bucket.add_lifecycle_rule(
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                    transition_after=Duration.days(30)
                )
            ]
        )

        # Datasets Bucket
        self.datasets_bucket = s3.Bucket(
            self, "DatasetsBucket",
            bucket_name=f"jal-saathi-datasets-{env_name}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
        )

        from aws_cdk import aws_secretsmanager as secretsmanager
        # Twilio Secret
        self.twilio_secret = secretsmanager.Secret(
            self, "TwilioSecret",
            secret_name=f"jal-saathi-twilio-{env_name}",
            description="Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SECRET_KEY for HMAC)",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"TWILIO_ACCOUNT_SID": "dummy", "TWILIO_AUTH_TOKEN": "dummy", "TWILIO_SECRET_KEY": "dummy"}',
                generate_string_key="dummy_key"
            )
        )

        # Tag all resources in this stack
        Tags.of(self).add("Project", "jal-saathi")
