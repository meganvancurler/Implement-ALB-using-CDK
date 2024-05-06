from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    core
)
from constructs import Construct


class ServerStack(core.Stack):

    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Web Server Security Group
        web_sg = ec2.SecurityGroup(
            self, "WebServerSG",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for web servers"
        )
        web_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP traffic")

        # RDS Security Group
        rds_sg = ec2.SecurityGroup(
            self, "RDSSG",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for RDS"
        )
        rds_sg.add_ingress_rule(web_sg, ec2.Port.tcp(3306), "Allow MySQL traffic from web servers")

        # Launch EC2 Instances in Public Subnets
        web_servers = []
        public_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets
        for idx, subnet in enumerate(public_subnets):
            instance = ec2.Instance(
                self, f"WebServer{idx+1}",
                instance_type=ec2.InstanceType("t2.micro"),
                machine_image=ec2.MachineImage.latest_amazon_linux(),
                vpc=vpc,
                vpc_subnet=ec2.SubnetSelection(subnets=[subnet]),
                security_group=web_sg
            )
            web_servers.append(instance)

        # Create an RDS Instance in Private Subnets
        rds_instance = rds.DatabaseInstance(
            self, "RDSInstance",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_26
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[rds_sg],
            multi_az=True,
            allocated_storage=20,
            max_allocated_storage=100,
            instance_type=ec2.InstanceType("t3.micro"),
            removal_policy=core.RemovalPolicy.DESTROY,
            delete_automated_backups=True,
        )

        # Create ALB
        alb = elbv2.ApplicationLoadBalancer(
            self, "ALB",
            vpc=vpc,
            internet_facing=True,
            security_group=web_sg
        )

        # Create ALB Listener
        listener = alb.add_listener("Listener", port=80, open=True)

        # Add EC2 instances as ALB targets
        listener.add_targets(
            "WebServerTargets",
            port=80,
            targets=[elbv2.InstanceTarget(instance) for instance in web_servers]
        )
