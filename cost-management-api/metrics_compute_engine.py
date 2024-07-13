from google.cloud import compute_v1
from google.cloud import monitoring_v3
from datetime import datetime, timedelta
from openai_client import get_nlp_response
from dotenv import load_dotenv
import os 
from google.oauth2 import service_account 
from google.protobuf import duration_pb2
from google.protobuf import timestamp_pb2

load_dotenv()
project = os.getenv('PROJECT_ID')  
credentials = service_account.Credentials.from_service_account_file(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
 
compute_client = compute_v1.InstancesClient(credentials=credentials)
monitoring_client = monitoring_v3.MetricServiceClient(credentials=credentials)
snapshot_client = compute_v1.SnapshotsClient(credentials=credentials) 

def list_instances(project, zone):
    instance_client = compute_v1.InstancesClient(credentials=credentials)
    request = compute_v1.ListInstancesRequest(project=project, zone=zone)
    response = instance_client.list(request=request)

    instances = []
    for instance in response:
        instances.append(instance)

    return instances 

def get_cpu_utilization(instance_name, project):
    interval = monitoring_v3.TimeInterval()
    now = datetime.utcnow()

    end_time = timestamp_pb2.Timestamp()
    end_time.FromDatetime(now)
    interval.end_time = end_time

    start_time = timestamp_pb2.Timestamp()
    start_time.FromDatetime(now - timedelta(days=7))
    interval.start_time = start_time

    aggregation = monitoring_v3.Aggregation(
        alignment_period=duration_pb2.Duration(seconds=3600),
        per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
    )

    results = monitoring_client.list_time_series(
        request={
            "name": f"projects/{project}",
            "filter": f'metric.type = "compute.googleapis.com/instance/cpu/utilization" AND resource.labels.instance_id = "{instance_name}"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            "aggregation": aggregation,
        }
    )

    utilizations = []
    for result in results:
        for point in result.points:
            utilizations.append(point.value.double_value)

    if utilizations:
        return sum(utilizations) / len(utilizations)
    return 0

def find_idle_underutilized_instances(instances, project): 
    for instance in instances:
        instance_name = instance.name
        cpu_utilization = get_cpu_utilization(instance_name, project)
        scheduling = instance.scheduling

        if cpu_utilization < 0.1: 
            problem = f"Instance: {instance_name} is underutilized with CPU Utilization: {cpu_utilization}"
            prompt = "How to manage underutilized instances in Google Cloud? Give details on how to identify and manage underutilized instances. Make sure to include the steps to analyze the CPU utilization and memory usage of instances. If there are any best practices or tools that can be used, please provide the details."
            answer = get_nlp_response(prompt) 
            return problem, answer
        elif cpu_utilization > 0.5 and scheduling.preemptible:
            problem = f"Instance: {instance_name} is overutilized with CPU Utilization: {cpu_utilization}"
            prompt = "How to manage overutilized instances in Google Cloud? Give details on how to identify and manage overutilized instances. Make sure to include the steps to analyze the CPU utilization and memory usage of instances. If there are any best practices or tools that can be used, please provide the details."
            answer = get_nlp_response(prompt) 
            return problem, answer
    return None, None
 
def get_network_egress(instance_name, project): 
    interval = monitoring_v3.TimeInterval()
    now = datetime.utcnow()

    end_time = timestamp_pb2.Timestamp()
    end_time.FromDatetime(now)
    interval.end_time = end_time

    start_time = timestamp_pb2.Timestamp()
    start_time.FromDatetime(now - timedelta(days=7))
    interval.start_time = start_time

    aggregation = monitoring_v3.Aggregation(
        alignment_period=duration_pb2.Duration(seconds=3600),
        per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
    )

    monitoring_client = monitoring_v3.MetricServiceClient()

    results = monitoring_client.list_time_series(
        request={
            "name": f"projects/{project}",
            "filter": f'metric.type = "compute.googleapis.com/instance/network/received_bytes_count" AND resource.labels.instance_id = "{instance_name}"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            "aggregation": aggregation,
        }
    )

    total_egress = 0
    for result in results:
        for point in result.points:
            total_egress += point.value.int64_value

    return total_egress / (1024 ** 3)  # Convert to GB 

def find_high_data_transfer_instances(instances, project): 
    for instance in instances:
        instance_name = instance.name
        network_egress = get_network_egress(instance_name, project)
        
        if network_egress and network_egress > 100:
            problem = f"Instance: {instance_name} has high data transfer egress: {network_egress} GB"
            prompt = "How to manage high data transfer egress in Google Cloud? Give details on how to reduce the data transfer costs. Make sure to include the steps to identify the instances that are generating high data transfer egress. If there are any best practices or tools that can be used, please provide the details."
            answer = get_nlp_response(prompt) 
            return problem, answer
    return None, None


def get_disk_io(instance_name, project):
    interval = monitoring_v3.TimeInterval()
    now = datetime.utcnow()
    interval.end_time.seconds = int(now.timestamp())
    interval.end_time.nanos = 0
    interval.start_time.seconds = int((now - timedelta(days=7)).timestamp())
    interval.start_time.nanos = 0

    aggregation = monitoring_v3.Aggregation(
        alignment_period={"seconds": 86400},  # 1 day
        per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
    )

    filters = [
        f'metric.type = "compute.googleapis.com/instance/disk/read_bytes_count" AND resource.labels.instance_id = "{instance_name}"',
        f'metric.type = "compute.googleapis.com/instance/disk/write_bytes_count" AND resource.labels.instance_id = "{instance_name}"'
    ]

    total_read_bytes = 0
    total_write_bytes = 0

    for filter_query in filters:
        results = monitoring_client.list_time_series(
            request={
                "name": f"projects/{project}",
                "filter": filter_query,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSerieslist_log_groupsView.FULL,
                "aggregation": aggregation,
            }
        )

        for result in results:
            for point in result.points:
                if "read_bytes_count" in filter_query:
                    total_read_bytes += point.value.int64_value
                else:
                    total_write_bytes += point.value.int64_value
    return total_read_bytes, total_write_bytes

def list_snapshots(project_id):
    snapshots = []  
    request = compute_v1.ListSnapshotsRequest(project=project_id) 

    for snapshot in snapshot_client.list(request=request):
        snapshots.append({
            'name': snapshot.name,
            'size_gb': snapshot.disk_size_gb,
            'creation_timestamp': snapshot.creation_timestamp
        }) 
    return snapshots
 
def find_large_snapshots(snapshots): 
    for snapshot in snapshots:
        if snapshot and "size_gb" in snapshot and snapshot["size_gb"] > 10:
            problem = f"Snapshot: {snapshot['name']} is large with size: {snapshot['size_gb']} GB"
            prompt = "How to manage large snapshots in Google Cloud? Give details on how to reduce the size of snapshots. Make sure to include the steps to identify the snapshots that are taking up large amounts of storage. If there are any best practices or tools that can be used, please provide the details."
            answer = get_nlp_response(prompt) 
            return problem, answer
    return None, None
 
def find_inefficient_disk_usage(instances, project): 
    for instance in instances:
        if instance["status"] == "RUNNING":
            instance_name = instance.name
            total_read_bytes, total_write_bytes = get_disk_io(instance_name, project)
            total_io_gb = (total_read_bytes + total_write_bytes) / (1024 ** 3)  # Convert to GB

            if total_io_gb < 1:  # Threshold for low disk usage in GB
                problem = f"Instance: {instance_name} has low disk usage: {total_io_gb:.2f} GB"
                prompt = "How to manage inefficient disk usage in Google Cloud? Give details on how to optimize disk usage. Make sure to include the steps to identify the instances with low disk usage. If there are any best practices or tools that can be used, please provide the details."
                answer = get_nlp_response(prompt) 
                return problem, answer
    return None, None


def check_compute_engine(): 
    instances = list_instances(project, "europe-west1-b")
    
    # Over-Provisioned Resources && Idle or Underutilized Instances
    overprovisioned_instances = find_idle_underutilized_instances(instances, project) 

    # High Data Transfer Costs
    high_data_transfer_instances = find_high_data_transfer_instances(instances, project)

    # Inefficient Use of Disk Storage
    snapshot_list = list_snapshots(project)
    inefficient_disk_usage = find_inefficient_disk_usage(instances, snapshot_list)

    # Large Amounts of Backups and Snapshots
    large_snapshots = find_large_snapshots(inefficient_disk_usage)

    results = {
        "overprovisioned_instances": overprovisioned_instances,
        "high_data_transfer_instances": high_data_transfer_instances, 
        "inefficient_disk_usage": inefficient_disk_usage,
        "large_snapshots": large_snapshots
    }
    return results 

