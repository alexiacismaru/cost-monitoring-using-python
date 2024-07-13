import boto3 
from dotenv import load_dotenv
import os

# todo: check permissions
 
load_dotenv()
 
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = 'eu-north-1' 
 
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

trusted_advisor_client = session.client('support')
compute_optimizer_client = session.client('compute-optimizer')

def get_trusted_advisor_checks():
    response = trusted_advisor_client.describe_trusted_advisor_checks(language='en')
    return response

checks = get_trusted_advisor_checks()
for check in checks['checks']:
    if 'Low Utilization Amazon EC2 Instances' in check['name']:
        check_id = check['id']
        break

response = trusted_advisor_client.describe_trusted_advisor_check_result(checkId=check_id)
underutilized_instances = response['result']['flaggedResources']
print(underutilized_instances)

def get_compute_optimizer_recommendations():
    response = compute_optimizer_client.get_ec2_instance_recommendations()
    return response

recommendations = get_compute_optimizer_recommendations()
print(recommendations)
