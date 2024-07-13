import boto3
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os 
from openai_client import get_nlp_response 
 
load_dotenv()
 
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
 
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

cloudwatch = session.client('cloudwatch')
ec2_client = session.client('ec2')
ce_client = session.client('ce')
autoscaling_client = boto3.client('autoscaling')

def get_all_instances():
    instances = []
    paginator = ec2_client.get_paginator('describe_instances')
    for page in paginator.paginate():
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance)
    return instances

def get_instance_id():
    instance_ids = []
    paginator = ec2_client.get_paginator('describe_instances')
    for page in paginator.paginate():
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
    return instance_ids

'''
General function to get instance metrics from CloudWatch
'''
def get_instance_metrics(metric_name, namespace, dimensions, statistics): 
    response = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=dimensions,
        StartTime= datetime.utcnow() - timedelta(days=1),
        EndTime= datetime.utcnow(),
        Period=3600,
        Statistics=statistics
    )
    return response['Datapoints'] 

def get_cpu_average(instance_id) :
    response = get_instance_metrics('CPUUtilization', 'AWS/EC2', [{'Name': 'InstanceId', 'Value': instance_id}], ['Average'])
 
    datapoints = response['Datapoints'] 
    total_utilization = sum([datapoint['Average'] for datapoint in datapoints])
    average_utilization = total_utilization / len(datapoints)

    if average_utilization < 20:
        problem = f"Instance {instance_id} is potentially over-provisioned or underutilized."
        prompt = ("How to optimize CPU utilization in Amazon EC2 instances?",
                  "Give details on how to identify and manage over-provisioned or", 
                  "underutilized instances. If there are any best practices or tools",
                  "that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None  

'''
High Data Transfer: Check if the instance has high data transfer (inbound or outbound)
'''
def high_data_transfer(instance_id):
    network_in = get_instance_metrics('NetworkIn', 'AWS/EC2', [{'Name': 'InstanceId', 'Value': instance_id}], ['Sum'])
    network_out = get_instance_metrics('NetworkOut', 'AWS/EC2', [{'Name': 'InstanceId', 'Value': instance_id}], ['Sum'])

    total_in = sum(data['Sum'] for data in network_in)
    total_out = sum(data['Sum'] for data in network_out)

    high_data_threshold = 1 * 1024 * 1024 * 1024 # threshold for high data transfer (1GB)

    if total_in > high_data_threshold: 
        problem = "High Inbound Data Transfer"
        prompt = ("How to reduce high inbound data transfer in Amazon EC2?",
                  "Give details on how to reduce the data transfer costs.",
                  "Make sure to include the steps to identify the instances", 
                  "that are generating high data transfer ingress. If there",
                  "are any best practices or tools that can be used, please ",
                  "provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer

    if total_out > high_data_threshold: 
        problem = "High Outbound Data Transfer"
        prompt = ("How to reduce high outbound data transfer in Amazon EC2?",
                  "Give details on how to reduce the data transfer costs.",
                  "Make sure to include the steps to identify the instances",
                  "that are generating high data transfer egress. If there",
                  "are any best practices or tools that can be used, please",
                  "provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None
 
'''
Get the instances and check if any of them is older than 180 days.
'''
def instance_age(): 
    threshold_date = datetime.now(timezone.utc) - timedelta(days=180) # any instance older then 180 days is considered old
    
    instances = get_all_instances()
    for instance in instances:
        launch_time = instance['LaunchTime'] 
    if launch_time < threshold_date:
        problem = f"Instance ID: {instance['InstanceId']}, Launch Time: {instance['LaunchTime']}, Age: {instance['AgeDays']} days"
        prompt = ("How to manage old or outdated instances in Amazon EC2?",
                    "Give details on how to identify and manage old instances.",
                    "Make sure to include the steps to analyze the instance age",
                    "and determine if they are outdated. If there are any best",
                    "practices or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None 

'''
Read operations retrieve data from storage attached to Amazon EC2 instances, 
such as EBS volumes or instance store volumes.

Write Operations store or save data to storage attached to Amazon EC2 instances, 
such as EBS volumes or instance store volumes.

Based on the read/write operations and volume size, identify unoptimized storage volumes.
''' 
def analyze_storage():
    instances = get_all_instances()
    unoptimized_volumes = []

    for instance in instances:
        instance_id = instance['InstanceId']
        volumes = ec2_client.describe_volumes(
            Filters=[
                {'Name': 'attachment.instance-id', 'Values': [instance_id]}
            ]
        )['Volumes']

        for volume in volumes:
            volume_id = volume['VolumeId']
            size = volume['Size']  # Size in GB
            volume_type = volume['VolumeType']

            read_ops_metrics = get_instance_metrics('VolumeReadOps', 'AWS/EBS', [{'Name': 'VolumeId', 'Value': volume_id}], ['Average'])
            write_ops_metrics = get_instance_metrics('VolumeWriteOps', 'AWS/EBS', [{'Name': 'VolumeId', 'Value': volume_id}], ['Average'])

            # Extract the metric values 
            read_ops_values = [metric['Value'] for metric in read_ops_metrics if 'Value' in metric]
            write_ops_values = [metric['Value'] for metric in write_ops_metrics if 'Value' in metric]

            # Calculate the average if there are any metrics
            read_ops = sum(read_ops_values) / len(read_ops_values) 
            write_ops = sum(write_ops_values) / len(write_ops_values)

            '''
            100 represents a low number of read/write operations per day and 500 represents a large volume size
            '''
            if (read_ops < 100 and write_ops < 100) or size > 500:
                unoptimized_volumes.append({
                    'InstanceId': instance_id,
                    'VolumeId': volume_id,
                    'VolumeType': volume_type,
                    'SizeGiB': size,
                    'ReadOps': read_ops,
                    'WriteOps': write_ops
                })

    for unoptimized_volume in unoptimized_volumes:
        problem = f"Instance ID: {unoptimized_volume['InstanceId']}, Volume ID: {unoptimized_volume['VolumeId']}, Volume Type: {unoptimized_volume['VolumeType']}, Size: {unoptimized_volume['SizeGiB']} GB, Read Ops: {unoptimized_volume['ReadOps']}, Write Ops: {unoptimized_volume['WriteOps']}"
        prompt = ("How to optimize storage attached to Amazon EC2 instances?",
                    "Give details on how to identify and manage unoptimized storage volumes.",
                    "Make sure to include the steps to analyze the storage usage and",
                    "performance metrics. If there are any best practices or tools",
                    "that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer

    return None, None

'''
Get all the snapshots for the account and get the start time of the snaphot.
If the snapshot is older than 180 days, it is considered outdated and it will let the user know
about an outdated snapshot.
'''
def get_all_snapshots():
    snapshots = []
    paginator = ec2_client.get_paginator('describe_snapshots')
    for page in paginator.paginate(OwnerIds=['self']):
        snapshots.extend(page['Snapshots'])
    return snapshots

def analyze_snapshot_usage(snapshots):
    excessive_snapshots = []
    threshold_date = datetime.utcnow() - timedelta(days=180)  # Example threshold for old snapshots

    for snapshot in snapshots:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId', 'Unknown')
        start_time = snapshot['StartTime']
        size = snapshot['VolumeSize']  # Size in GB

        if start_time < threshold_date:
            excessive_snapshots.append({
                'SnapshotId': snapshot_id,
                'VolumeId': volume_id,
                'StartTime': start_time,
                'SizeGiB': size
            })
        problem = f"Snapshot ID: {snapshot_id}, Volume ID: {volume_id}, Start Time: {start_time}, Size: {size} GB"
        prompt = ("How to manage excessive backup and snapshot storage in Amazon EC2?",
                    "Give details on how to identify and manage old snapshots.",
                    "Make sure to include the steps to analyze the snapshot age",
                    "and determine if they are outdated. If there are any best",
                    "practices or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer 
    return None, None  




def check_amazonec2(): 
    instance_ids = get_instance_id() 
    for instance_id in instance_ids:
        # High Data Transfer
        network_data = high_data_transfer(instance_id)
        # Overprovisioned instances and idle instances
        overprovisioned_instances = get_cpu_average(instance_id) 

    # Old or Outdated Instances  
    outdated = instance_age()

    # Unoptimized Storage Attached to Instances 
    unoptimized = analyze_storage()

    # Excessive Backup and Snapshot
    snapshots = get_all_snapshots() 
    snapshot_usage = analyze_snapshot_usage(snapshots)

    results = {
        'overprovisioned_instances': overprovisioned_instances,
        'network_data': network_data,
        'outdated': outdated,
        'unoptimized': unoptimized,
        'snapshot_usage': snapshot_usage
    }
    return results
 