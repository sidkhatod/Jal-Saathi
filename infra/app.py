#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.data_stack import DataStack
from stacks.table_stack import TableStack
from stacks.roles_stack import RolesStack

app = cdk.App()

# Get environment from context, default to 'dev'
env_name = app.node.try_get_context("env") or "dev"

# Setup the CDK environment
aws_env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region="ap-south-1"
)

data_stack = DataStack(
    app, 
    f"JalSaathiDataStack-{env_name}", 
    env=aws_env, 
    env_name=env_name
)

table_stack = TableStack(
    app, 
    f"JalSaathiTableStack-{env_name}", 
    env=aws_env,
    env_name=env_name
)

roles_stack = RolesStack(
    app, 
    f"JalSaathiRolesStack-{env_name}", 
    env=aws_env,
    env_name=env_name,
    photos_bucket=data_stack.photos_bucket,
    datasets_bucket=data_stack.datasets_bucket,
    farms_table=table_stack.farms_table,
    plots_table=table_stack.plots_table,
    observations_table=table_stack.observations_table,
    advisories_table=table_stack.advisories_table
)

app.synth()
