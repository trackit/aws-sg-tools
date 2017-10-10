import boto3
import argparse
import sys

def get_vpc_and_sg(ec2_ressources):
    for vpc in ec2_ressources.vpcs.all():
        for security_group in vpc.security_groups.all():
            yield vpc, security_group

def get_ip_permissions_vpc_and_sg(ec2_ressources, ip_permission_type):
    for vpc, security_group in get_vpc_and_sg(ec2_ressources):
        if ip_permission_type == "out":
            for ip_permission_egress in security_group.ip_permissions_egress:
                yield vpc, security_group, ip_permission_egress
        if ip_permission_type == "in":
            for ip_permission_ingress in security_group.ip_permissions:
                yield vpc, security_group, ip_permission_ingress

def main(args, session, data=None):
    ec2_ressources = session.resource('ec2')
    for vpc, security_group, ip_permission_ingress in get_ip_permissions_vpc_and_sg(ec2_ressources, "in"):
        if "FromPort" in ip_permission_ingress and ip_permission_ingress['FromPort'] == 0:
            print "Security group with id {} and group name {} on VPC {} has a too broad inbound rule (port range is set to 0, i.e. all ports are open)".format(security_group.id, security_group.group_name, vpc.id)
    for vpc, security_group, ip_permission_egress in get_ip_permissions_vpc_and_sg(ec2_ressources, "out"):
        if "ToPort" in ip_permission_egress and ip_permission_egress['ToPort'] == 0:
            print "Security group with id {} and group name {} on VPC {} has a too broad outboud rule (port range is set to 0, i.e. all ports are open)".format(security_group.id, security_group.group_name, vpc.id)
    if data is not None:
        return []
