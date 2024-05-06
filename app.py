#!/usr/bin/env python3
import aws_cdk as cdk
from my_cdk_project.network_stack import NetworkStack
from my_cdk_project.server_stack import ServerStack

app = cdk.App()

# Create the network stack
network_stack = NetworkStack(app, "NetworkStack")

# Create the server stack
ServerStack(app, "ServerStack", vpc=network_stack.vpc)

app.synth()
