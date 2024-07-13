import boto3
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import os 
from collections import defaultdict
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
s3 = session.client('s3')
logs_client = boto3.client('logs')

def get_s3_buckets(): 
    response = s3.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    return buckets 

'''
Get the bucket items and check if they have been modified in the last 30 days.
'''
def get_s3_inneficient_objects(bucket_name): 
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name) 

    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                storage_class = obj.get('StorageClass', 'STANDARD')
                last_modified = obj['LastModified']
                current_time = datetime.now(timezone.utc)
                days_since_last_modified = (current_time - last_modified).days

                if storage_class == 'STANDARD' and days_since_last_modified > 30:
                    problem = f"Inefficient Storage Class in {bucket_name}"
                    prompt = ("How to optimize storage class in Amazon S3?",
                                "Give details on how to reduce the cost of storage by",
                                "optimizing the storage class. Make sure to include the steps",
                                "to identify the objects that are not being accessed frequently.",
                                "If is there any documentation that can be referred to, please provide",
                                "the link. And list some other reasons why there might be an overspending problem on Amazon S3.")
                    answer = get_nlp_response(prompt)
                    return problem, answer 
    return None, None    

def get_s3_object_versions(bucket_name): 
    paginator = s3.get_paginator('list_object_versions')
    page_iterator = paginator.paginate(Bucket=bucket_name)
    version_info = defaultdict(list)
    
    for page in page_iterator:
        if 'Versions' in page:
            for version in page['Versions']:
                key = version['Key']
                size = version['Size']
                version_id = version['VersionId']
                is_latest = version['IsLatest']
                version_info[key].append({
                    'version_id': version_id,
                    'size': size,
                    'is_latest': is_latest
                })
    return version_info 
 
def list_multipart_uploads(bucket_name): 
    response = s3.list_multipart_uploads(Bucket=bucket_name)
    
    if 'Uploads' in response: 
        problem = f"Incomplete Multipart Uploads in {bucket_name}"
        prompt = ("How to manage incomplete multipart uploads in Amazon S3?",
                    "Give details on how to reduce the number of incomplete",
                    "uploads. Make sure to include the steps to identify the",
                    "uploads that are not completed. If is there any documentation",
                    "that can be referred to, please provide the link. And list some",
                    "other reasons why there might be an overspending problem on Amazon S3.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None 

def calculate_log_stats(log_files):
    total_size = sum(log['Size'] for log in log_files)
    log_count = len(log_files)
    return total_size, log_count    
    
'''
Get the log group name for CloudTrail logs and check if the logs are generated excessively. 
'''
def analyze_replication(buckets):
    replication_info = {}

    ''' TODO:
    The function loops through each bucket name in the buckets list.
    It calls get_s3_object_versions(bucket_name) to get version information for objects in the bucket (assuming this function is defined elsewhere).
    It iterates over the items in version_info, where key is the object key and versions is a list of versions for that object.
    It populates replication_info with this data.
    '''
    for bucket_name in buckets:
        version_info = get_s3_object_versions(bucket_name)
        for key, versions in version_info.items():
            if key not in replication_info:
                replication_info[key] = {}
            if bucket_name not in replication_info[key]:
                replication_info[key][bucket_name] = []
            replication_info[key][bucket_name].extend(versions)

    '''TODO:
    The function iterates over the replication_info dictionary.
    It checks if an object key (key) is present in more than one bucket (len(bucket_info) > 1).
    If high replication is detected:
    It creates a problem string describing the high replication issue for that object key.
    It defines a prompt tuple with detailed questions about managing high replication in S3.
    It calls get_nlp_response(prompt) to get an NLP-generated response (assuming this function is defined elsewhere).
    It returns the problem string and the answer from the NLP response.
    If no high replication is detected for any object, it returns None, None.
    '''
    for key, bucket_info in replication_info.items():
        if len(bucket_info) > 1:
            problem  = f"High Replication for {key}"
            prompt = ("How to manage high replication in Amazon S3?",
                        "Give details on how to reduce the number of replicated",
                        "objects. Make sure to include the steps to identify the",
                        "objects that are being replicated multiple times. If is",
                        "there any documentation that can be referred to, please",
                        "provide the link. And list some other reasons why there might",
                        "be an overspending problem on Amazon S3.")
            answer = get_nlp_response(prompt)
            return problem, answer
    return None, None 

def get_s3_request_metrics(bucket_name, start_time, end_time):
    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/S3',
        MetricName='NumberOfRequests',
        Dimensions=[
            {'Name': 'BucketName', 'Value': bucket_name},
            {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,  # 1 hour intervals
        Statistics=['Sum']
    )
    return metrics['Datapoints'] 

def analyze_requests(bucket_name): 
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    metrics = get_s3_request_metrics(bucket_name, start_time, end_time)

    total_requests = sum([datapoint['Sum'] for datapoint in metrics])
    average_requests_per_hour = total_requests / 24   

    if average_requests_per_hour > 10000:
        problem = f"Excessive Requests in {bucket_name}"
        prompt = ("How to manage excessive requests in Amazon S3?",
                    "Give details on how to reduce the number of requests.",
                    "Make sure to include the steps to identify the requests",
                    "that are generating high frequency data points. If is there",
                    "any documentation that can be referred to, please provide the",
                    "link. And list some other reasons why there might be an overspending",
                    "problem on Amazon S3.")
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None 




def check_amazons3(): 
    buckets = get_s3_buckets()
    for bucket in buckets: 
        # Multipart Uploads Not Completed  
        multiple_uploads = list_multipart_uploads(bucket)

        # Inefficient Storage Classes 
        inefficient_objects = get_s3_inneficient_objects(bucket)  

        # Excessive Requests 
        excessive_requests = analyze_requests(bucket) 

    # High Replication
    replication_info = analyze_replication(buckets) 

    results = { 
        "multiple_uploads": multiple_uploads,
        "replication_info": replication_info, 
        "inefficient_objects": inefficient_objects,
        "excessive_requests": excessive_requests
    }
    return results
