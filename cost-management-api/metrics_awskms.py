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
kms_client = boto3.client('kms')
cloudtrail_client = boto3.client('cloudtrail')

def check_number_of_keys(): 
    cmk_count = 0 
    paginator = kms_client.get_paginator('list_keys')

    for page in paginator.paginate():
        cmk_count += len(page['Keys']) 
    
    if cmk_count > 5:
        problem = f"High Number of Customer Managed Keys ({cmk_count})"
        prompt = "How to manage a high number of Customer Managed Keys in AWS KMS? Give details on how to manage the keys in AWS KMS. Make sure to include the steps to identify the keys that are not being used. If is there any documentation that can be referred to, please provide the link. And list some other reasons why there might be an overspending problem on AWS KMS."
        answer = get_nlp_response(prompt)
        return problem, answer
    return cmk_count
 
def get_kms_key_operations():  
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    # Define the KMS operations to look for
    kms_operations = [
        'Encrypt',
        'Decrypt',
        'GenerateDataKey',
        'GenerateDataKeyWithoutPlaintext',
        'ReEncrypt',
        'DescribeKey',
        'CreateKey',
        'ScheduleKeyDeletion',
        'CancelKeyDeletion'
    ] 
    operation_counts = {operation: 0 for operation in kms_operations} 

    paginator = cloudtrail_client.get_paginator('lookup_events')
    for page in paginator.paginate(
        LookupAttributes=[{'AttributeKey': 'EventSource', 'AttributeValue': 'kms.amazonaws.com'}],
        StartTime=start_time,
        EndTime=end_time
    ):
        for event in page['Events']:
            event_name = event['EventName']
            if event_name in kms_operations:
                operation_counts[event_name] += 1

    for operation in kms_operations.items():
        if len(operation) > 10:
            problem = f"High Number of {operation} Operations in the last 24 hours."
            prompt = "How to handle keys in AWS KMS? Give details on how to manage the keys in AWS KMS. Make sure to include the steps to identify the keys that are not being used. If is there any documentation that can be referred to, please provide the link. And list some other reasons why there might be an overspending problem on AWS KMS."
            answer = get_nlp_response(prompt)
            return problem, answer
    return None, None 
 
def check_unnecessary_key_rotations(days):  
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    rotation_counts = {} 
    paginator = cloudtrail_client.get_paginator('lookup_events')
    for page in paginator.paginate(
        LookupAttributes=[{'AttributeKey': 'EventSource', 'AttributeValue': 'kms.amazonaws.com'}],
        StartTime=start_time,
        EndTime=end_time
    ):
        for event in page['Events']:
            event_name = event['EventName']
            if event_name == 'RotateKey':
                key_id = event['Resources'][0]['ResourceName']
                if key_id in rotation_counts:
                    rotation_counts[key_id] += 1
                else:
                    rotation_counts[key_id] = 1
    return rotation_counts 

def key_rotation():
    key_rotations = check_unnecessary_key_rotations(days=365)     
    for key_id, count in key_rotations.items():
        if count > 1:
            problem = f"Key {key_id} has been rotated {count} times in the past year."
            prompt = "How to handle unnecessary key rotations in AWS KMS? Give details on how to manage the keys in AWS KMS. Make sure to include the steps to identify the keys that are not being used. If is there any documentation that can be referred to, please provide the link. And list some other reasons why there might be an overspending problem on AWS KMS."
            answer = get_nlp_response(prompt)
            return problem, answer
    return None, None




def check_awskms():
    # High Number of Customer Managed Keys  
    keys = check_number_of_keys()

    # Misuse of Key Operations
    key_operations = get_kms_key_operations()

    # Unnecessary Key Rotations
    unnecessary_key_rotations = key_rotation()

    results = {
        "keys": keys,
        "key_operations": key_operations,
        "key_rotations": unnecessary_key_rotations
    }
    return results