from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct

class TableStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # On-demand billing for all tables
        billing_mode = dynamodb.BillingMode.PAY_PER_REQUEST

        self.farms_table = dynamodb.Table(
            self, "FarmsTable",
            table_name=f"jal-saathi-farms-{env_name}",
            partition_key=dynamodb.Attribute(name="farmer_id", type=dynamodb.AttributeType.STRING),
            billing_mode=billing_mode,
            removal_policy=RemovalPolicy.RETAIN
        )

        self.plots_table = dynamodb.Table(
            self, "PlotsTable",
            table_name=f"jal-saathi-plots-{env_name}",
            partition_key=dynamodb.Attribute(name="farm_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="plot_id", type=dynamodb.AttributeType.STRING),
            billing_mode=billing_mode,
            removal_policy=RemovalPolicy.RETAIN
        )

        self.observations_table = dynamodb.Table(
            self, "ObservationsTable",
            table_name=f"jal-saathi-observations-{env_name}",
            partition_key=dynamodb.Attribute(name="plot_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="observation_timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=billing_mode,
            removal_policy=RemovalPolicy.RETAIN
        )

        self.advisories_table = dynamodb.Table(
            self, "AdvisoriesTable",
            table_name=f"jal-saathi-advisories-{env_name}",
            partition_key=dynamodb.Attribute(name="plot_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="week_timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=billing_mode,
            removal_policy=RemovalPolicy.RETAIN
        )
