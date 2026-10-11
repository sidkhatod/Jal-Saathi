import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from stacks.auth_stack import AuthStack
from stacks.data_stack import DataStack
from stacks.table_stack import TableStack
from stacks.roles_stack import RolesStack
from stacks.api_stack import ApiStack

def test_auth_stack_resources():
    app = cdk.App()
    auth_stack = AuthStack(app, "TestAuthStack", env_name="test")
    template = Template.from_stack(auth_stack)

    # 1. Verify UserPool exists with proper config
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "UserPoolName": "jal-saathi-users-test",
        "Policies": {
            "PasswordPolicy": {
                "MinimumLength": 6,
                "RequireLowercase": False,
                "RequireNumbers": False,
                "RequireSymbols": False,
                "RequireUppercase": False
            }
        }
    })

    # 2. Verify SPA Web Client exists without client secret
    template.has_resource_properties("AWS::Cognito::UserPoolClient", {
        "ClientName": "jal-saathi-web-client-test",
        "GenerateSecret": False
    })

def test_api_stack_includes_upload_lambda():
    app = cdk.App()
    env_name = "test"
    data_stack = DataStack(app, "TestDataStack", env_name=env_name)
    table_stack = TableStack(app, "TestTableStack", env_name=env_name)
    roles_stack = RolesStack(
        app, "TestRolesStack",
        env_name=env_name,
        photos_bucket=data_stack.photos_bucket,
        datasets_bucket=data_stack.datasets_bucket,
        farms_table=table_stack.farms_table,
        plots_table=table_stack.plots_table,
        observations_table=table_stack.observations_table,
        advisories_table=table_stack.advisories_table,
        twilio_secret=data_stack.twilio_secret
    )
    api_stack = ApiStack(
        app, "TestApiStack",
        env_name=env_name,
        lambda_role=roles_stack.lambda_role,
        farms_table=table_stack.farms_table,
        plots_table=table_stack.plots_table,
        observations_table=table_stack.observations_table,
        advisories_table=table_stack.advisories_table,
        photos_bucket=data_stack.photos_bucket,
        twilio_secret_arn=data_stack.twilio_secret.secret_arn
    )

    template = Template.from_stack(api_stack)

    # 1. Verify Presigned Upload Lambda exists
    template.has_resource_properties("AWS::Lambda::Function", {
        "FunctionName": "jal-saathi-upload-test",
        "Handler": "upload_handler.handler",
        "Runtime": "python3.12"
    })

    # 2. Verify Function URLs exist (Webhook + Upload)
    template.resource_count_is("AWS::Lambda::Url", 2)