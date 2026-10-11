from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_location as location,
    CfnOutput,
    Duration
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, lambda_role: iam.IRole, 
                 farms_table, plots_table, observations_table, advisories_table, photos_bucket, twilio_secret_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 2. Amazon Location Service Place Index
        self.place_index = location.CfnPlaceIndex(
            self, "PlaceIndex",
            index_name=f"jal-saathi-place-index-{env_name}",
            data_source="Esri",
            description="Place index for reverse geocoding farmer pins"
        )

        # 3. Webhook Lambda Function
        self.webhook_lambda = _lambda.Function(
            self, "WebhookLambda",
            function_name=f"jal-saathi-webhook-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="webhook.handler",
            code=_lambda.Code.from_asset("../backend", exclude=[".venv", ".pytest_cache", "__pycache__"]),
            role=lambda_role,
            timeout=Duration.seconds(30),
            environment={
                "ENV": env_name,
                "TWILIO_SECRET_ARN": twilio_secret_arn,
                "PLACE_INDEX_NAME": self.place_index.index_name,
                "FARMS_TABLE": farms_table.table_name,
                "PLOTS_TABLE": plots_table.table_name,
                "OBSERVATIONS_TABLE": observations_table.table_name,
                "ADVISORIES_TABLE": advisories_table.table_name,
                "PHOTOS_BUCKET": photos_bucket.bucket_name
            }
        )

        # 4. HTTP API via Function URL (simplest, no alpha dependencies)
        self.function_url = self.webhook_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )

        # Output the API URL
        CfnOutput(
            self, "WebhookApiUrl",
            value=self.function_url.url,
            description="URL of the webhook API"
        )
