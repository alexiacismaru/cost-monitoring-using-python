import boto3
from dotenv import load_dotenv
import os
from openai_client import get_nlp_response
from datetime import datetime
 
load_dotenv()
 
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
 
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)
client = session.client('config') 

def get_resource_count(): 
    response = client.get_discovered_resource_counts()

    if response['totalDiscoveredResources'] > 10:
        problem = f"High Number of Resources in AWS Config ({response['totalDiscoveredResources']})"
        prompt = ("How to manage a High number of resources in AWS Config? Give details on how to reduce",
                    "the number of resources. Make sure to include the steps to identify the resources that",
                    "are not being used. If is there any documentation that can be referred to, please provide",
                    "the link. And list some other reasons why there might be an overspending problem on AWS Config.")                                                                       
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None

def get_custom_rules(): 
    paginator = client.get_paginator('describe_config_rules')
    custom_rules = []
    
    for page in paginator.paginate():
        for rule in page['ConfigRules']:
            if rule['Source']['Owner'] == 'CUSTOM_LAMBDA':
                custom_rules.append(rule)
    return custom_rules

def evaluate_custom_rule_usage(): 
    custom_rules = get_custom_rules()
    inefficient_rules = []
    
    for rule in custom_rules:
        rule_name = rule['ConfigRuleName']
        evaluation_response = client.get_compliance_details_by_config_rule(
            ConfigRuleName=rule_name,
            ComplianceTypes=['NON_COMPLIANT'],
            Limit=100
        )
        
        non_compliant_count = len(evaluation_response['EvaluationResults'])
        if non_compliant_count == 0:
            inefficient_rules.append(rule_name)

    if inefficient_rules:
        problem = f"Inefficient Custom Rules in AWS Config ({len(inefficient_rules)} rules)"
        prompt = ("How to manage inefficient custom rules in AWS Config? Give details on how to optimize",
                    "the custom rules. Make sure to include the steps to identify the rules that are not",
                    "performing well. If is there any documentation that can be referred to, please provide",
                    "the link. And list some other reasons why there might be an overspending problem on AWS Config.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None  

def check_retention_period(): 
    response = client.describe_delivery_channel_status()
    if 'DeliveryChannelsStatus' in response and len(response['DeliveryChannelsStatus']) > 0:
        status = response['DeliveryChannelsStatus'][0]
        if 'ConfigHistoryDeliveryInfo' in status:
            return status['ConfigHistoryDeliveryInfo']['lastSuccessfulTime']
    return None 

def retention_period():   
    response = client.describe_configuration_recorder_status() 
    recorder_statuses = response['ConfigurationRecordersStatus']

    for status in recorder_statuses:
        if not status['recording']:
            problem = f"Configuration Recorder {status['name']} is not recording."
            prompt = "How to handle a Configuration Recorder that is not recording? Give details on how to troubleshoot and fix the issue. Make sure to include the steps to identify the root cause of the problem. If is there any documentation that can be referred to, please provide the link. And list some other reasons why there might be an overspending problem on AWS Config."
            answer = get_nlp_response(prompt) 
            continue

    last_successful_delivery = check_retention_period()
    if last_successful_delivery: 
        current_time = datetime.now(last_successful_delivery.tzinfo)
        retention_period_days = (current_time - last_successful_delivery).days 

    if retention_period_days > 30:
        problem = "Retention period exceeds the threshold of 30 days."
        prompt = "How to manage a high retention period in AWS Config? Give details on how to reduce the retention period. Make sure to include the steps to identify the configuration items that are not being used. If is there any documentation that can be referred to, please provide the link. And list some other reasons why there might be an overspending problem on AWS Config."
        answer = get_nlp_response(prompt) 
        return problem, answer
    return None, None




def check_awsconfig():
    # High Number of Recorded Resources 
    resource_count = get_resource_count()

    # Inefficient Use of Custom Rules
    inneficient_rules = evaluate_custom_rule_usage()
    
    # Retention Period of Configuration Items
    retention_period = retention_period()
    
    results = {
        "resource_count": resource_count,
        "inefficient_rules": inneficient_rules,
        "retention_period": retention_period
    }
    return results
