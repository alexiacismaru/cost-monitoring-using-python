import boto3 
from dotenv import load_dotenv
import os
from openai_client import get_nlp_response
from datetime import datetime, timedelta
 
load_dotenv()
 
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
 
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

ec2_client = session.client('ec2')
logs_client = session.client('logs')
cloudwatch_client = session.client('cloudwatch') 

def list_nat_gateways():
    response = ec2_client.describe_nat_gateways()
    nat_gateways = response['NatGateways']
    return nat_gateways
 
def get_metrics(namespace, metric_name, dimenions, start_time, end_time, statistics):
    response = cloudwatch_client.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=dimenions,
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,  # 1 hour
        Statistics=statistics,
    )
    return response['Datapoints'] 
 
def list_unused_eips(): 
    # retrieve a description of the Elastic IP addresses that are allocated to your AWS account
    response = ec2_client.describe_addresses()
    unused_eips = []
    
    for address in response['Addresses']:
        # If the Elastic IP address is not associated with any instance or network interface it's considered unused
        if 'InstanceId' not in address and 'NetworkInterfaceId' not in address and 'AssociationId' not in address:
            unused_eips.append(address['PublicIp'])

    if unused_eips:
        problem = f"Unused Elastic IP Addresses: {unused_eips}"
        prompt = ("How to manage unused Elastic IP addresses in Amazon VPC?",
                    "Give details on how to identify and release the unused Elastic IP addresses.",
                    "Make sure to include the steps to analyze the Elastic IP addresses that are not",
                    "associated with any instances or network interfaces. If there are any best practices",
                    "or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None 

def list_vpn_connections():
    response = ec2_client.describe_vpn_connections()
    vpn_connections = response['VpnConnections']
    return vpn_connections 

'''
Get the metrics for the VPN connections and check if the data transfer is high.
If the data transfer is higher than 1,000,000 bytes, return a problem and ask for a solution.
'''
def get_high_data_transfer(): 
    vpn_connections = list_vpn_connections()
    for vpn_connection in vpn_connections:
        vpn_connection_id = vpn_connection['VpnConnectionId']
        network_in = get_metrics('AWS/VPN', 'NetworkPacketsIn', [{'Name': 'VpnId', 'Value': vpn_connection_id}], start_time, end_time, ['Sum'])
        network_out = get_metrics('AWS/VPN', 'NetworkPacketsOut', [{'Name': 'VpnId', 'Value': vpn_connection_id}], start_time, end_time, ['Sum']) 
        
        for datapoint in network_in: 
            if datapoint['Sum'] > 1000000: 
                problem = f"High data transfer detected (IN) at {datapoint['Timestamp']}: {datapoint['Sum']}"
                prompt = ("How to handle high data transfer in Amazon VPC?",
                            "Give details on how to reduce the amount of data transferred over VPN connections.",
                            "Make sure to include the steps to analyze the data transfer and network traffic of",
                            "VPN connections. If there are any best practices or tools that can be used, please provide the details.")
                answer = get_nlp_response(prompt)
                return problem, answer 
    
        for datapoint in network_out: 
            if datapoint['Sum'] > 1000000: 
                problem = f"High data transfer detected (OUT) at {datapoint['Timestamp']}: {datapoint['Sum']}"
                prompt = ("How to handle high data transfer in Amazon VPC?",
                            "Give details on how to reduce the amount of data transferred over VPN connections.",
                            "Make sure to include the steps to analyze the data transfer and network traffic of",
                            "VPN connections. If there are any best practices or tools that can be used, please provide the details.")
                answer = get_nlp_response(prompt)
                return problem, answer
    return None, None

def list_vpc_endpoints():
    paginator = ec2_client.get_paginator('describe_vpc_endpoints')
    response_iterator = paginator.paginate()
    
    vpc_endpoints = []
    for page in response_iterator:
        vpc_endpoints.extend(page['VpcEndpoints'])
    return vpc_endpoints
 
def count_vpc_endpoints():
    vpc_endpoints = list_vpc_endpoints()
    endpoint_count = len(vpc_endpoints)

    if endpoint_count > 100:
        problem = f"High Number of Endpoints ({endpoint_count})"
        prompt = ("How to manage a high number of VPC endpoints in Amazon VPC?",
                    "Give details on how to reduce the number of VPC endpoints.",
                    "Make sure to include the steps to analyze the endpoints that are generating high traffic.",
                    "If there are any best practices or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None  

def analyze_route_tables():
    response = ec2_client.describe_route_tables()
    route_tables = response['RouteTables']
    
    for rt in route_tables: 
        for route in rt['Routes']: 
            # If the route does not have a NetworkInterfaceId, InstanceId, NatGatewayId, or VpcPeeringConnectionId, it is considered unused. 
            if 'NetworkInterfaceId' not in route and 'InstanceId' not in route and 'NatGatewayId' not in route and 'VpcPeeringConnectionId' not in route:
                problem = f'Unused route: Destination: {route["DestinationCidrBlock"]}, Target: {route.get("GatewayId", "None")}'
                prompt = ("How to handle an unused route? Give details on how to identify and manage",
                            "unused routes in route tables. Make sure to include the steps to analyze the routes that",
                            "are not being used. If there are any best practices or tools that can be used, please provide the details.")
                answer = get_nlp_response(prompt)
                return problem, answer
            
            '''
            If the route has a State of blackhole, it is considered a blackhole route. Return a problem and ask for a solution.
            A blackhole route is a route that drops the traffic without informing the source. It is used to filter unwanted traffic.
            '''
            if route.get('State') == 'blackhole':
                problem = f'Blackhole route: Destination: {route["DestinationCidrBlock"]}, Target: {route.get("GatewayId", "None")}'
                prompt = ("How to handle a blackhole route? Give details on how to identify and manage blackhole",
                            "routes in route tables. Make sure to include the steps to analyze the routes that are not",
                            "functioning properly. If there are any best practices or tools that can be used, please provide the details.")
                answer = get_nlp_response(prompt)
                return problem, answer
        return None, None 
 
def analyze_network_acls():
    response = ec2_client.describe_network_acls()
    network_acls = response['NetworkAcls']
    
    for nacl in network_acls: 
        for entry in nacl['Entries']: 
            '''
            If the rule allows all traffic it is considered an overly permissive rule. 
            A permissive rule allows all traffic to pass through, which can be a security risk.
            ''' 
            if entry['RuleAction'] == 'allow' and entry['CidrBlock'] == '0.0.0.0/0':
                problem = f'Overly permissive rule: RuleNumber: {entry["RuleNumber"]}, Protocol: {entry["Protocol"]}, Ports: {entry.get("PortRange", "All")}, Action: {entry["RuleAction"]}'
                prompt = ("How to handle an overly permissive rule in network ACLs? Give details on how to identify",
                            "and manage overly permissive rules in network ACLs. Make sure to include the steps to analyze",
                            "the rules that are allowing traffic to all IP addresses. If there are any best practices or tools",
                            "that can be used, please provide the details.")
                answer = get_nlp_response(prompt)
                return problem, answer
            '''
            If the entry is an egress rule and allows all traffic it is considered an overly permissive egress rule.
            '''
            if entry['Egress'] and entry['CidrBlock'] == '0.0.0.0/0':
                problem = f'Overly permissive egress rule: RuleNumber: {entry["RuleNumber"]}, Protocol: {entry["Protocol"]}, Ports: {entry.get("PortRange", "All")}, Action: {entry["RuleAction"]}'
                prompt = ("How to handle an overly permissive egress rule in network ACLs? Give details on how to identify",
                            "and manage overly permissive egress rules in network ACLs. Make sure to include the steps to analyze",
                            "the egress rules that are allowing traffic to all IP addresses. If there are any best practices or tools",
                            "that can be used, please provide the details.")
                answer = get_nlp_response(prompt)
                return problem, answer
        return None, None 
    
def analyze_security_groups():
    response = ec2_client.describe_security_groups()
    security_groups = response['SecurityGroups']

    for sg in security_groups:
        # Check the number of incoming and outgoing rules in the security group
        num_ingress_rules = len(sg['IpPermissions'])
        num_egress_rules = len(sg['IpPermissionsEgress'])
 
        if num_ingress_rules > 50 or num_egress_rules > 10:
            problem = f'Security Group {sg["GroupId"]} has numerous rules:'
            prompt = ("How to handle a security group with numerous rules? Give details on how to manage",
                        "security groups with a large number of ingress and egress rules. Make sure to include the steps",
                        "to analyze the rules that are generating high traffic. If there are any best practices or tools that",
                        "can be used, please provide the details.")
            answer = get_nlp_response(prompt)
            return problem, answer
         
        # For each ingress rule, it check if there are more than 10 CIDR blocks (which define IP ranges).
        for permission in sg['IpPermissions']:
            num_cidr_blocks = len(permission.get('IpRanges', []))
            if num_cidr_blocks > 10:
                problem = f'Security Group {sg["GroupId"]} has complex ingress CIDR blocks.'
                prompt = ("How to handle a security group with complex ingress CIDR blocks? Give details on how to simplify",
                            "the ingress CIDR blocks. Make sure to include the steps to identify the CIDR blocks that are generating",
                            "high traffic. If there are any best practices or tools that can be used, please provide the details.")
                answer = get_nlp_response(prompt)
                return problem, answer
            
        # Check if there are more than 10 CIDR blocks in the egress rules.
        for permission in sg['IpPermissionsEgress']:
            num_cidr_blocks = len(permission.get('IpRanges', []))
            if num_cidr_blocks > 10:
                problem = f'Security Group {sg["GroupId"]} has complex egress CIDR blocks.'
                prompt = ("How to handle a security group with complex egress CIDR blocks? Give details on how to simplify",
                            "the egress CIDR blocks. Make sure to include the steps to identify the CIDR blocks that are generating",
                            "high traffic. If there are any best practices or tools that can be used, please provide the details.") 
                answer = get_nlp_response(prompt)
                return problem, answer
    return None, None

def inefficient_nat_gateways():
    nat_gateways = list_nat_gateways()
    for nat_gateway in nat_gateways:
        nat_gateway_id = nat_gateway['NatGatewayId'] 

        metrics = ['BytesIn', 'BytesOut', 'PacketsIn', 'PacketsOut']
        for metric in metrics:
            datapoints = get_metrics('AWS/NATGateway', metric, [{'Name': 'NatGatewayId', 'Value': nat_gateway_id}], start_time, end_time, ['Sum'])
            total = sum(dp['Sum'] for dp in datapoints)  

    if total < 1e9: # if the total data transfer is less than 1GB
        problem = f"Inefficient Use of NAT Gateway {nat_gateway_id}"
        prompt = ("How to optimize NAT gateways in Amazon VPC? Give details on how to reduce the amount of data transferred over NAT gateways.",
                    "Make sure to include the steps to analyze the data transfer and network traffic of NAT gateways. If there are any best practices",
                    "or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None 
    
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=1)

def inefficient_vpn_connections():
    vpn_connections = list_vpn_connections()

    for vpn_connection in vpn_connections:
        vpn_connection_id = vpn_connection['VpnConnectionId']
        
        metrics = ['TunnelDataIn', 'TunnelDataOut']
        for metric in metrics:
            datapoints = get_metrics('AWS/VPN', metric, [{'Name': 'VpnId', 'Value': vpn_connection_id}], start_time, end_time, ['Sum'])
            total = sum(dp['Sum'] for dp in datapoints) 
            
    if total < 1e6: # if the total data transfer is less than 1MB
        problem = f"Inefficient Use of VPN Connections in {vpn_connection_id}"
        prompt = ("How to optimize VPN connections in Amazon VPC? Give details on how to reduce the amount",
                   "of data transferred over VPN connections. Make sure to include the steps to analyze the data transfer",
                    "and network traffic of VPN connections. If there are any best practices",
                    "or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None 

def traffic_monitoring():
    response = ec2_client.describe_flow_logs() 
    flow_logs = response['FlowLogs']

    for flow_log in flow_logs:
        log_group_name = flow_log['LogGroupName'] 
        
        datapoints = get_metrics('AWS/Logs', 'IncomingBytes', [{'Name': 'LogGroupName', 'Value': log_group_name}], start_time, end_time, ['Sum'])
        total_bytes = sum(dp['Sum'] for dp in datapoints)   
        
    if total_bytes > 1e9: # if the total incoming bytes is greater than 1GB
        problem = f"Excessive Traffic Monitoring in {log_group_name}"
        prompt = ("How to optimize traffic monitoring in Amazon VPC? Give details on how to reduce the amount of data",
                     "transferred for traffic monitoring. Make sure to include the steps to analyze the incoming traffic logs",
                      "and network traffic. If there are any best practices or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None




def check_amazonvpc():
    # Over-Provisioned NAT Gateways
    overprovisioned_gateways = inefficient_nat_gateways()

    # Unused Elastic IP Addresses
    unused_eips = unused_eips() 

    # Inefficient Use of VPN Connections 
    vpn_connections = inefficient_vpn_connections() 

    # Excessive Traffic Monitoring
    excessive_traffic_monitoring = traffic_monitoring()

    # Inneficient Route Tables and Network ACLs 
    route_tables = analyze_route_tables() 
    network_acls = analyze_network_acls()

    # Numerous and Complex Security Group Rules 
    security_groups = analyze_security_groups()

    # High Data Transfer   
    high_data_transfer = get_high_data_transfer()

    results = {
        "overprovisioned_gateways": overprovisioned_gateways,
        "unused_eips": unused_eips,
        "vpn_connections": vpn_connections, 
        "traffic_monitoring": excessive_traffic_monitoring,
        "route_tables": route_tables,
        "network_acls": network_acls,
        "security_groups": security_groups,
        "high_data_transfer": high_data_transfer
    }
    return results 