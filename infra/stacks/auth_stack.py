from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Cognito User Pool configured for farmer-friendly access
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name=f"jal-saathi-users-{env_name}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                username=True,
                phone=True,
                email=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=False,
                phone=False
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=6,
                require_digits=False,
                require_symbols=False,
                require_uppercase=False,
                require_lowercase=False
            ),
            account_recovery=cognito.AccountRecovery.PHONE_WITHOUT_MFA_AND_EMAIL,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY
        )

        # 2. SPA Web Client (no secret, suitable for Vite React web app)
        self.user_pool_client = self.user_pool.add_client(
            "WebClient",
            user_pool_client_name=f"jal-saathi-web-client-{env_name}",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            prevent_user_existence_errors=True
        )

        # Outputs
        CfnOutput(
            self, "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID for Jal-Saathi"
        )

        CfnOutput(
            self, "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Web Client ID for Jal-Saathi SPA"
        )
