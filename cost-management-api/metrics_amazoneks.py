import boto3
from datetime import datetime, timedelta
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

eks_client = session.client('eks')
ec2_client = session.client('ec2')
cloudwatch_client = session.client('cloudwatch')
elb_client = session.client('elbv2')
logs_client = session.client('logs')
autoscaling_client = session.client('autoscaling')

def get_eks_clusters():
    response = eks_client.list_clusters()
    return response['clusters']

def get_nodegroup_info(cluster_name):
    response = eks_client.list_nodegroups(clusterName=cluster_name)
    nodegroups = response['nodegroups']
    nodegroup_info = []
    
    for nodegroup in nodegroups:
        response = eks_client.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup)
        nodegroup_info.append(response['nodegroup'])
    return nodegroup_info

'''
An Amazon EC2 Auto Scaling group (ASG) contains a collection of EC2 instances that share similar characteristics and 
are treated as a logical grouping for the purposes of fleet management and dynamic scaling. (source: AWS Documentation)
'''
def get_instance_ids_from_asg(asg_name):
    response = autoscaling_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    instance_ids = []
    for asg in response['AutoScalingGroups']:
        for instance in asg['Instances']:
            instance_ids.append(instance['InstanceId'])
    return instance_ids 

def get_instance_ids_from_eks_cluster(cluster_name):
    eks_client.describe_cluster(name=cluster_name)
    nodegroups = eks_client.list_nodegroups(clusterName=cluster_name)['nodegroups']
    instance_ids = []
    
    for nodegroup in nodegroups:
        nodegroup_info = eks_client.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup)
        asg_name = nodegroup_info['nodegroup']['resources']['autoScalingGroups'][0]['name']
        instance_ids += get_instance_ids_from_asg(asg_name)
    
    return instance_ids

# Universal method to get instance metrics from CloudWatch
def get_instance_metrics(metric_name, namespace, dimensions, statistics): 
    response = cloudwatch_client.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=dimensions,
        StartTime= datetime.utcnow() - timedelta(days=1),
        EndTime= datetime.utcnow(),
        Period=3600,
        Statistics=statistics
    )
    return response['Datapoints']  

'''
Calculate the average CPU and memory utilization of the instances in the Amazon EKS cluster.
If the average CPU utilization is less than 20% and the average memory utilization is less than 20%,
the resources are considered over-provisioned and idle and the user is given a prompt to handle the issue.
'''
def analyze_over_provisioned_resources():
    clusters = get_eks_clusters()
    
    for cluster in clusters: 
        nodegroups = get_nodegroup_info(cluster)
        
        for nodegroup in nodegroups:
            asg_name = nodegroup['resources']['autoScalingGroups'][0]['name']
            instance_ids = get_instance_ids_from_asg(asg_name)
            
            for instance_id in instance_ids: 
                cpu_metrics = get_instance_metrics('CPUUtilization', 'AWS/EC2', [{'Name': 'InstanceId', 'Value': instance_id}], ['Average'])
                memory_metrics = get_instance_metrics('MemoryUtilization', 'CWAgent', [{'Name': 'InstanceId', 'Value': instance_id}], ['Average'])  

                if cpu_metrics and memory_metrics:
                    avg_cpu_utilization = sum(dp['Average'] for dp in cpu_metrics) / len(cpu_metrics)
                    avg_memory_utilization = sum(dp['Average'] for dp in memory_metrics) / len(memory_metrics)
                    
                    if avg_cpu_utilization < 20 and avg_memory_utilization < 20:
                        problem = "Over-Provisioned and Idle Resources Detected"
                        prompt = ("How to handle over-provisioned or idle resources in Amazon EKS? "
                                  "Give details on how to identify and manage over-provisioned or "
                                  "idle resources. Make sure to include the steps to analyze the CPU "
                                  "utilization and memory usage of instances. If there are any best practices "
                                  "or tools that can be used, please provide the details.")
                        answer = get_nlp_response(prompt)
                        return problem, answer
    return None, None

'''
Get the network data transfer metrics for the instances in the Amazon EKS cluster.
If the sum of the network data transfer (inbound and outbound) is greater than 1 GB,
the user is given a prompt to reduce data transfer costs in Amazon EKS.
'''
def analyze_high_data_transfer():
    clusters = get_eks_clusters()
    
    for cluster in clusters: 
        nodegroups = get_nodegroup_info(cluster)
        
        for nodegroup in nodegroups:
            asg_name = nodegroup['resources']['autoScalingGroups'][0]['name']
            instance_ids = get_instance_ids_from_asg(asg_name)
            
            for instance_id in instance_ids:
                network_in = get_instance_metrics('NetworkIn', 'AWS/EC2', [{'Name': 'InstanceId', 'Value': instance_id}], ['Sum'])
                network_out = get_instance_metrics('NetworkOut', 'AWS/EC2', [{'Name': 'InstanceId', 'Value': instance_id}], ['Sum']) 
                network_in_sum = sum([dp['Sum'] for dp in network_in])
                network_out_sum = sum([dp['Sum'] for dp in network_out])

    if network_in_sum > 1e9 or network_out_sum > 1e9:  # 1 GB
        problem = "High Data Transfer Costs Detected in Amazon EKS"
        prompt = ("How to reduce data transfer costs in Amazon EKS?", 
                    "Give details on how to reduce data transfer costs in Amazon EKS.", 
                    "Make sure to include the steps to analyze the data transfer costs and", 
                    "identify the resources that are generating high data transfer costs. If there are",
                    "any best practices or tools that can be used, please provide the details.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None  

'''
Load balancers improve application performance by increasing response time and reducing network latency. 
They perform several critical tasks such as the following: Distribute the load evenly between servers to improve 
application performance. Redirect client requests to a geographically closer server to reduce latency. (source: AWS Documentation)

Analyze the load balancer configuration for the instances and their health in the Amazon EKS cluster.
If an instance is not part of the cluster or is not healthy in the load balancer, 
the user is given a prompt to manage load balancers for Amazon EKS.
'''
def analyze_load_balancer_configuration():
    clusters = get_eks_clusters()

    load_balancer_response = elb_client.describe_load_balancers()
    load_balancers = load_balancer_response['LoadBalancers']

    for cluster in clusters: 
        cluster_instance_ids = get_instance_ids_from_eks_cluster(cluster)

        for lb in load_balancers:
            lb_arn = lb['LoadBalancerArn'] 

            target_groups_response = elb_client.describe_target_groups(LoadBalancerArn=lb_arn)
            target_groups = target_groups_response['TargetGroups']

            for tg in target_groups:
                tg_arn = tg['TargetGroupArn']

                targets_response = elb_client.describe_target_health(TargetGroupArn=tg_arn)
                targets = targets_response['TargetHealthDescriptions']

                for target in targets:
                    instance_id = target['Target']['Id']
                    health_status = target['TargetHealth']['State']

                    if instance_id not in cluster_instance_ids:
                        problem = f"Instance {instance_id} is not part of the cluster."
                        prompt = ("How to manage load balancers for Amazon EKS? "
                                  "Give details on how to manage load balancers for Amazon EKS. "
                                  "Make sure to include the steps to configure load balancers and troubleshoot "
                                  "common issues. If there are any best practices or tools that can be used, please provide the details.")
                        answer = get_nlp_response(prompt)
                        return problem, answer

                    if health_status != 'healthy':
                        problem = f"Instance {instance_id} is not healthy in the load balancer."
                        prompt = ("How to manage load balancers for Amazon EKS? "
                                  "Give details on how to manage load balancers for Amazon EKS. "
                                  "Make sure to include the steps to configure load balancers and troubleshoot "
                                  "common issues. If there are any best practices or tools that can be used, please provide the details.")
                        answer = get_nlp_response(prompt)
                        return problem, answer
    return None, None

'''
Analyze the cluster monitoring and optimization for the instances in the Amazon EKS cluster.
If the CPU utilization is over 80%, memory utilization is over 80%, or the data transfer is over 1 GB,
the user is given a prompt to optimize the monitoring and resources in Amazon EKS.
'''
def check_cloudwatch_logs(log_group_name):
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    return bool(response['logGroups'])

def analyze_cluster_monitoring_and_optimization():
    clusters = get_eks_clusters() 
    
    for cluster in clusters: 
        cluster_instance_ids = get_instance_ids_from_eks_cluster(cluster)
 
        for instance_id in cluster_instance_ids:
            cpu_metrics = get_instance_metrics('CWAgent', 'cpu_usage_total', [{'Name': 'InstanceId', 'Value': instance_id}], ['Average'])
            memory_metrics =  get_instance_metrics('CWAgent', 'mem_used_percent', [{'Name': 'InstanceId', 'Value': instance_id}], ['Average'])
            network_in_metrics = get_instance_metrics('AWS/EC2', 'NetworkIn', [{'Name': 'InstanceId', 'Value': instance_id}] , ['Average'])
            network_out_metrics = get_instance_metrics('AWS/EC2', 'NetworkOut', [{'Name': 'InstanceId', 'Value': instance_id}], ['Average']) 

    # insufficient monitoring
    if not cpu_metrics or not memory_metrics:
        problem = f"Insufficient monitoring for instance {instance_id}. Ensure CloudWatch agent is installed and configured."
        prompt = "How to ensure proper monitoring for Amazon EKS instances? Give details on how to ensure proper monitoring for Amazon EKS instances. Make sure to include the steps to install and configure the CloudWatch agent. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer

    # optimization
    if cpu_metrics and any(dp['Average'] > 80 for dp in cpu_metrics):
        problem = f"Instance {instance_id} is overutilized for CPU."
        prompt = "How to optimize CPU usage in Amazon EKS? Give details on how to optimize CPU usage in Amazon EKS. Make sure to include the steps to analyze the CPU utilization and identify the resources that are overutilized. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer
    
    if memory_metrics and any(dp['Average'] > 80 for dp in memory_metrics): 
        problem = "Instance is overutilized for memory."
        prompt = "How to optimize memory usage in Amazon EKS?"
        answer = get_nlp_response(prompt)
        return problem, answer
    
    if network_in_metrics and any(dp['Average'] > 1e9 for dp in network_in_metrics):  # 1 GB
        problem = f"High data transfer for instance {instance_id}."
        prompt = "How to reduce data transfer costs in Amazon EKS? Give details on how to reduce data transfer costs in Amazon EKS. Make sure to include the steps to analyze the data transfer costs and identify the resources that are generating high data transfer costs. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer
    if network_out_metrics and any(dp['Average'] > 1e9 for dp in network_out_metrics):
        problem = f"High data transfer for instance {instance_id}."
        prompt = "How to reduce data transfer costs in Amazon EKS? Give details on how to reduce data transfer costs in Amazon EKS. Make sure to include the steps to analyze the data transfer costs and identify the resources that are generating high data transfer costs. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer
    
    # collect logs
    log_group_name = f"/aws/eks/{cluster}/cluster"
    if not check_cloudwatch_logs(log_group_name): 
        problem = f"Insufficient logging for cluster {cluster}. Ensure CloudWatch logging is enabled."
        prompt = "How to enable logging for Amazon EKS? Give details on how to enable logging for Amazon EKS. Make sure to include the steps to configure CloudWatch logging and troubleshoot common issues. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None

def analyze_metrics(cluster_name): 
    metric_names = ['podCount', 'nodeCount'] 

    for metric_name in metric_names:
        data_points = get_instance_metrics(metric_name, 'AWS/EKS', [{'Name': 'ClusterName', 'Value': cluster_name}], ['Sum'])
        
        total_sum = sum(dp['Sum'] for dp in data_points) 
        
    if total_sum > 10000:  
        problem = f"High {metric_name} count for cluster {cluster_name}."
        prompt = "How to optimize monitoring in Amazon EKS? Give details on how to optimize monitoring in Amazon EKS. Make sure to include the steps to analyze the metrics and identify the resources that are generating high metric counts. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None

def get_ebs_volumes(instance_id):
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    volumes = []
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            for block_device in instance['BlockDeviceMappings']:
                volume_id = block_device['Ebs']['VolumeId']
                volumes.append(volume_id)
    return volumes

def get_volume_metrics(volume_id):
    metrics = ['VolumeReadBytes', 'VolumeWriteBytes', 'VolumeIdleTime']  
    volume_metrics = {}

    for metric in metrics:
        response = get_instance_metrics(metric, 'AWS/EBS', [{'Name': 'VolumeId', 'Value': volume_id}], ['Sum'])  
        total = sum(dp['Sum'] for dp in response)
        volume_metrics[metric] = total 
    return volume_metrics

'''
Get the EBS volumes attached to the instances in the Amazon EKS cluster.
If the volume is idle for more than 12 hours, the user is given a prompt to optimize storage in Amazon EKS.
'''
def analyze_persistent_volumes():
    clusters = get_eks_clusters()
    
    for cluster in clusters: 
        nodegroups = get_nodegroup_info(cluster)
        
        for nodegroup in nodegroups:
            asg_name = nodegroup['resources']['autoScalingGroups'][0]['name']
            instance_ids = get_instance_ids_from_asg(asg_name)
            
            for instance_id in instance_ids:
                volume_ids = get_ebs_volumes(instance_id)
                
                for volume_id in volume_ids:
                    volume_metrics = get_volume_metrics(volume_id)
                     
                    if volume_metrics['VolumeIdleTime'] > 43200:  # 12 hours 
                        problem = f"Volume {volume_id} is idle for more than 12 hours."
                        prompt = ("How to optimize storage in Amazon EKS? "
                                  "Give details on how to optimize storage in Amazon EKS. Make "
                                  "sure to include the steps to analyze the storage usage and "
                                  "identify the resources that are generating high storage costs. "
                                  "If there are any best practices or tools that can be used, "
                                  "please provide the details.")
                        answer = get_nlp_response(prompt)
                        return problem, answer
    return None, None




def check_amazoneks():
    # Over-Provisioned and Idle Resources 
    overprovisioned_resources = analyze_over_provisioned_resources() 

    # High Data Transfer
    high_data_transfer = analyze_high_data_transfer()

    # Misconfigured Load Balancers
    load_balancer = analyze_load_balancer_configuration()

    # Cluster Monitoring and Optimization
    cluster_monitoring = analyze_cluster_monitoring_and_optimization()

    # Inefficient Use of Storage
    persistent_volumes = analyze_persistent_volumes()

    results = { 
        'overprovisioned_resources': overprovisioned_resources, 
        'high_data_transfer': high_data_transfer,
        'load_balancer': load_balancer,
        'cluster_monitoring': cluster_monitoring,
        'persistent_volumes': persistent_volumes
    }
    return results