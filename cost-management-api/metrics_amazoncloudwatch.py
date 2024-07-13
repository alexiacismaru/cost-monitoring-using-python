import boto3
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
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
logs_client = session.client('logs') 

def list_all_metrics():
    paginator = cloudwatch.get_paginator('list_metrics')
    metrics = []
    for response in paginator.paginate():
        metrics.extend(response['Metrics'])
    return metrics

def check_excessive_metrics():
    all_metrics = list_all_metrics()
    
    if len(all_metrics) > 100:  # Excessive number of metrics threshold
        problem = "Excessive Metrics Collection"
        prompt = ("How to fix excessive metrics collection in Amazon Cloudwatch? "
                  "Give details on how to reduce the number of metrics. Make sure "
                  "to include the steps to identify the metrics that are not being "
                  "used. If there is any documentation that can be referred to, "
                  "please provide the link. And list some other reasons why there "
                  "might be an overspending problem on Amazon Cloudwatch.")
        answer = get_nlp_response(prompt)
        return problem, answer   
    return None, None 

'''
Log Group: A log group is a collection of log streams that share the same settings, such as retention policies and access control.
Log groups typically represent a specific application, service, or resource.

Log Stream: A log stream is a sequence of log events from the same source, such as a specific instance of an application or an individual server. 
Each log stream is uniquely identified within a log group.
''' 
def list_log_groups():
    paginator = logs_client.get_paginator('describe_log_groups')
    log_groups = []
    for response in paginator.paginate():
        log_groups.extend(response['logGroups'])
    
    if len(log_groups) > 100:
        problem = "Excessive Number of Log Groups"
        prompt = ("How to fix excessive number of log groups in Amazon Cloudwatch?", 
                  "Give details on how to reduce the number of log groups. Make sure",
                  "to include the steps to identify the log groups that are not being",
                  "used. If is there any documentation that can be referred to, please",
                  "provide the link. And list some other reasons why there might be an",
                  "overspending problem on Amazon Cloudwatch.")
        answer = get_nlp_response(prompt)
        return problem, answer 
    return None, None

def get_get_log_group_names():
    log_group_names = []
    paginator = logs_client.get_paginator('describe_log_groups')
    for response in paginator.paginate():
        for log_group in response['logGroups']:
            log_group_names.append(log_group['logGroupName'])
    return log_group_names

def list_log_streams(log_group_name):
    paginator = logs_client.get_paginator('describe_log_streams')
    log_streams = []
    for response in paginator.paginate(logGroupName=log_group_name):
        log_streams.extend(response['logStreams'])
    
    if len(log_streams) > 100:
        problem = "Excessive Number of Log Streams"
        prompt = ("How to fix excessive number of log streams in Amazon Cloudwatch?",
                    "Give details on how to reduce the number of log streams. Make sure",
                    "to include the steps to identify the log streams that are not being",
                    "used. If is there any documentation that can be referred to, please",
                    "provide the link. And list some other reasons why there might be an",
                    "overspending problem on Amazon Cloudwatch.")
        answer = get_nlp_response(prompt)
        return problem, answer 
    return None, None

def high_data_points(metrics):
    start_time = datetime.now() - timedelta(minutes=60)
    end_time = datetime.now()
    
    for metric in metrics:
        namespace = metric['Namespace']
        metric_name = metric['MetricName']
        dimensions = metric['Dimensions']

        result = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # Period set to one day (24 hours * 60 minutes * 60 seconds)
            Statistics=['Sum']
        )
        
        if len(result['Datapoints']) > 100: 
            problem = "High Frequency Data Points"
            prompt = (
                "How to fix high frequency data points in Amazon Cloudwatch?", 
                "Give details on how to reduce the frequency of data points. Make sure",
                "to include the steps to identify the metrics that are generating high",
                "frequency data points. If is there any documentation that can be referred",
                "to, please provide the link. And list some other reasons why there might",
                "be an overspending problem on Amazon Cloudwatch."
            )
            answer = get_nlp_response(prompt)
            return problem, answer 
    return None, None




def check_amazoncloudwatch():
    metrics = list_all_metrics()
    # Excessive number of metrics
    excessive_metrics = check_excessive_metrics()

    #  High volume of logs
    log_groups = list_log_groups()
    log_names = get_get_log_group_names()
    for log_name in log_names:
        log_streams = list_log_streams(log_name)

    # High frequency data points  
    high_frequency = high_data_points(metrics)

    results = {
        "excessive_metrics": excessive_metrics,
        "log_groups": log_groups,
        "log_streams": log_streams,
        "high_frequency": high_frequency
    } 
    return results 