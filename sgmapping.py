import boto3
import csv, StringIO
import argparse
import sys

def _check_if_in_list(dict_list, value, key):
    """Check if an elements exists in a list of dictionaries for a specific key/value pair"""
    if dict_list is None:
        return None
    return next((item for item in dict_list if item[key] == value), None)

def _get_sg_name(sg_name, session):
    """Returns the name of the security group from its id"""
    return session.resource("ec2").SecurityGroup(sg_name).group_name

def _build_functions_list():
    """Build and return a function list mapped to resources type"""
    return {"ec2-sg": _build_ec2_mapping_from_sg,
            "ec2-resources": _build_ec2_mapping_from_resources,
            "rds-sg": _build_rds_mapping_from_sg,
            "rds-resources": _build_rds_mapping_from_resources,
            "elbv2-sg": _build_elbv2_mapping_from_sg,
            "elbv2-resources": _build_elbv2_mapping_from_resources}

def _generate_elb_instances_and_sg(resource, session):
    """Generator to yield instances, security group and security group name for ELBV2"""
    for instance in resource.describe_load_balancers()["LoadBalancers"]:
        for security_group in instance.get("SecurityGroups", []):
            yield instance, security_group, _get_sg_name(security_group, session)

def _build_elbv2_mapping_from_resources(resource_to_analyse, result_dict, session):
    """Build the mapping Resources -> SG for ELBV2"""
    for elb_instance, security_group_id, security_group_name in _generate_elb_instances_and_sg(resource_to_analyse, session):
        resource_dict = _check_if_in_list(result_dict, elb_instance["LoadBalancerName"], "resource_id")
        if resource_dict is not None:
            resource_dict["sg_attached"].append({
                "sg_id": security_group_id,
                "sg_name": security_group_name
            })
        else:
            result_dict.append({
                "resource_id": elb_instance["LoadBalancerName"],
                "resource_type": "elb",
                "sg_attached": [{
                    "sg_id": security_group_id,
                    "sg_name": security_group_name
                }]
            })
    return result_dict

def _build_elbv2_mapping_from_sg(resource_to_analyse, result_dict, session):
    """Build the mapping SG -> resources for ELBV2"""
    for elb_instance, security_group_id, security_group_name in _generate_elb_instances_and_sg(resource_to_analyse, session):
        resource_dict = _check_if_in_list(result_dict, security_group_id, "sg_id")
        if resource_dict is not None:
            resource_dict["resources_attached"].append({
                "resource_id": elb_instance["LoadBalancerName"],
                "resource_type": "elb"
            })
        else:
            result_dict.append({
                "sg_id": security_group_id,
                "sg_name": security_group_name,
                "resources_attached": [{
                    "resource_id": elb_instance["LoadBalancerName"],
                    "resource_type": "elb"
                }]
            })
    return result_dict


def _generate_rds_instances_and_sg(resource, session):
    """Generator to yield instances, security group and security group name for RDS"""
    for db_instance in resource.describe_db_instances()["DBInstances"]:
        for security_group in db_instance["VpcSecurityGroups"]:
            yield db_instance, security_group, _get_sg_name(security_group["VpcSecurityGroupId"], session)

def _build_rds_mapping_from_resources(resource_to_analyse, result_dict, session):
    """Build the mapping Resources -> SG for RDS"""
    for db_instance, security_group, sg_name in _generate_rds_instances_and_sg(resource_to_analyse, session):
        resource_dict = _check_if_in_list(result_dict, db_instance["DBInstanceIdentifier"], "resource_id")
        if resource_dict is not None:
            resource_dict["sg_attached"].append({
                "sg_id": security_group["VpcSecurityGroupId"],
                "sg_name": sg_name
            })
        else:
            result_dict.append({
                "resource_id": db_instance["DBInstanceIdentifier"],
                "resource_type": "rds",
                "sg_attached": [{
                    "sg_id": security_group["VpcSecurityGroupId"],
                    "sg_name": sg_name
                }]
            })
    return result_dict
    
def _build_rds_mapping_from_sg(resource_to_analyse, result_dict, session):
    """Build the mapping SG -> resources for RDS"""
    for db_instance, security_group, sg_name in _generate_rds_instances_and_sg(resource_to_analyse, session):
        resource_dict = _check_if_in_list(result_dict, security_group["VpcSecurityGroupId"], "sg_id")
        if resource_dict is not None:
            resource_dict["resources_attached"].append({
                "resource_id": db_instance["DBInstanceIdentifier"],
                "resource_type": "rds"
            })
        else:
            result_dict.append({
                "sg_id": security_group["VpcSecurityGroupId"],
                "sg_name": sg_name,
                "resources_attached": [{
                    "resource_id": db_instance["DBInstanceIdentifier"],
                    "resource_type": "rds"
                }]
            })
    return result_dict

def _generate_ec2_instance_and_sg(resource):
    """Generator to yield instances, security group for EC2"""
    for instance in resource.instances.all():
        for security_group in instance.security_groups:
            yield instance, security_group

def _build_ec2_mapping_from_resources(resource_to_analyse, result_dict, session):
    """Build the mapping Resources -> SG for EC2"""
    for instance, security_group in _generate_ec2_instance_and_sg(resource_to_analyse):
        resource_dict = _check_if_in_list(result_dict, instance.id, "resource_id")
        if resource_dict is not None:
            resource_dict["sg_attached"].append({
                "sg_id": security_group["GroupId"],
                "sg_name": security_group["GroupName"]
            })
        else:
            result_dict.append({
                "resource_id": instance.id,
                "resource_type": "ec2",
                "resource_name": "" if _check_if_in_list(instance.tags, "Name", "Key") is None else _check_if_in_list(instance.tags, "Name", "Key").get("Value", ""),
                "sg_attached": [{
                    "sg_id": security_group["GroupId"],
                    "sg_name": security_group["GroupName"]
                }]
            })
    return result_dict

def _build_ec2_mapping_from_sg(resource_to_analyse, result_dict, session):
    """Build the mapping SG -> resources for EC2"""
    for instance, security_group in _generate_ec2_instance_and_sg(resource_to_analyse):
        sg_dict = _check_if_in_list(result_dict, security_group["GroupId"], "sg_id")
        if sg_dict is not None:
            sg_dict["resources_attached"].append({
                "resource_id": instance.id,
                "resource_type": "ec2",
                "resource_name": "" if _check_if_in_list(instance.tags, "Name", "Key") is None else _check_if_in_list(instance.tags, "Name", "Key").get("Value", "")
            })
        else:
            result_dict.append({
                "sg_id": security_group["GroupId"],
                "sg_name": security_group["GroupName"],
                "resources_attached": [{
                    "resource_id": instance.id,
                    "resource_type": "ec2",
                    "resource_name": "" if _check_if_in_list(instance.tags, "Name", "Key") is None else _check_if_in_list(instance.tags, "Name", "Key").get("Value", "")
                }]
            })
    return result_dict

def _generate_csv(data, header_name):
    si = StringIO.StringIO()
    writer = csv.DictWriter(si, header_name)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return si.getvalue()

def _create_flattened_csv_from_sg(mapping):
    """Flattens the data to generate the csv, in the sg -> resources mapping direction"""
    data = [{
        "sg_id": security_group["sg_id"],
        "sg_name": security_group["sg_name"],
        "resource_id": resource["resource_id"],
        "resource_type": resource["resource_type"],
        "resource_name": resource.get("resource_name", "")}
        for security_group in mapping
        for resource in security_group["resources_attached"]]
    header = ["sg_id", "sg_name", "resource_id", "resource_type", "resource_name"]
    print _generate_csv(data, header)[:-1]

def _create_flattened_csv_from_resources(mapping):
    """Flattends the data to generate the csv, in the resources -> sg mapping direction"""
    data = [{
        "resource_id": resource["resource_id"],
        "resource_type": resource["resource_type"],
        "resource_name": resource.get("resource_name", ""),
        "sg_id": security_group["sg_id"],
        "sg_name": security_group["sg_name"]}
        for resource in mapping
        for security_group in resource["sg_attached"]]
    header = ["resource_id", "resource_type", "resource_name", "sg_id", "sg_name"]
    print _generate_csv(data, header)[:-1]

def main(parsed_args, session, data=None):
    """ This program is used for mapping Security Groups to resources, and vice versa.

    It works for EC2, RDS and ELBV2 resources type.
    By default it will map in the direction Security Group -> resources.
    """
    reverse_mapping = parsed_args['reverse_direction']
    function_list = _build_functions_list()
    default_resources_to_map = [["ec2", session.resource("ec2")], ["rds", session.client("rds")], ["elbv2", session.client("elbv2")]]
    mapping = ([] if data is None else data) # If existing data is passed to the program, use it
    for resource_type in default_resources_to_map:
        try:
            mapping = function_list["{}-{}".format(resource_type[0], "sg" if not reverse_mapping else "resources")](resource_type[1], mapping, session)
        except KeyError as e:
            print ("Error, Security groups mapping for resource type {} are not implemented".format(resource_type[0]))
    if data is not None and 'finished' not in parsed_args: # Return the raw mapping data, or if finished print the results
        return mapping
    if not reverse_mapping:
        _create_flattened_csv_from_sg(mapping)
    else:
        _create_flattened_csv_from_resources(mapping)