from google.cloud import monitoring_v3
from google.oauth2 import service_account 
from dotenv import load_dotenv
import os  
from googleapiclient import discovery 
from kubernetes import client 
from googleapiclient import discovery
from datetime import datetime, timedelta
from openai_client import get_nlp_response
from google.cloud import container_v1
from google.cloud.monitoring_v3 import query

'''
To be able to run this code, you need to make sure that the Kubernetes cluster is running ($kubectl cluster-info) and the necessary permissions are set up.
'''
v1 = client.CoreV1Api()

load_dotenv()
project_id = os.getenv('PROJECT_ID')   
credentials = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
)

client = monitoring_v3.MetricServiceClient(credentials=credentials)
project_name = f"projects/{project_id}" 

service = discovery.build('container', 'v1', credentials=credentials)

clusters = service.projects().zones().clusters().list(projectId=project_id, zone='-').execute()  
nodes = v1.list_node().items
pods = v1.list_pod_for_all_namespaces().items

def setup_kubernetes_client(cluster):
    configuration = client.Configuration()
    configuration.host = f"https://{cluster.endpoint}"
    configuration.verify_ssl = False
    configuration.api_key = {"authorization": "Bearer " + cluster.master_auth.cluster_ca_certificate}
    client.Configuration.set_default(configuration)

def calculate_node_usage(nodes, pods):
    node_capacity = {}
    node_usage = {}

    for node in nodes:
        node_name = node.metadata.name
        capacity = node.status.capacity
        node_capacity[node_name] = {
            "cpu": int(capacity["cpu"]),
            "memory": int(capacity["memory"].replace("Ki", "")) // 1024
        }
        node_usage[node_name] = {"cpu": 0, "memory": 0}

    for pod in pods:
        for container in pod.spec.containers:
            requests = container.resources.requests
            if requests:
                node_name = pod.spec.node_name
                node_usage[node_name]["cpu"] += int(requests["cpu"].replace("m", ""))
                node_usage[node_name]["memory"] += int(requests["memory"].replace("Mi", ""))

    return node_capacity, node_usage

def node_over_provisioning(node_capacity, node_usage):
    for node, capacity in node_capacity.items():
        usage = node_usage[node]
        
    if usage['cpu'] < capacity['cpu'] // 2:
        problem = f"Node: {node} has  CPU: {usage['cpu']}m / {capacity['cpu']}m and  Memory: {usage['memory']}Mi / {capacity['memory']}Mi"
        prompt = "How to manage over-provisioned nodes in Kubernetes? Give details on how to identify and manage the over-provisioned nodes. Make sure to include the steps to analyze the CPU utilization and memory usage of the nodes. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer 
    return None, None

def get_node_pools(project_id, zone, cluster_id):
    client = container_v1.ClusterManagerClient()
    response = client.get_cluster(project_id=project_id, zone=zone, cluster_id=cluster_id)
    return response.node_pools

def get_node_metrics():
    api_instance = client.CustomObjectsApi()
    metrics = api_instance.list_cluster_custom_object(
        group="metrics.k8s.io",
        version="v1beta1",
        plural="nodes"
    )
    return metrics

def identify_excessive_high_performance_use(node_pools, metrics):
    high_perf_machine_types = ["n1-highcpu-32", "n1-highmem-64", "n1-standard-64", "n1-ultramem-40", "n1-ultramem-80"]

    for node_pool in node_pools:
        machine_type = node_pool.config.machine_type
        if machine_type in high_perf_machine_types:
            for item in metrics['items']:
                node_name = item['metadata']['name']
                if node_name.startswith(node_pool.name):
                    cpu_usage = int(item['usage']['cpu'].rstrip('n')) / (1000**3)  # Convert to cores
                    memory_usage = int(item['usage']['memory'].rstrip('Ki')) / (1024**2)  # Convert to Gi
                    cpu_capacity = int(item['capacity']['cpu'])  # Cores
                    memory_capacity = int(item['capacity']['memory'].rstrip('Ki')) / (1024**2)  # Gi

                    cpu_utilization = cpu_usage / cpu_capacity
                    memory_utilization = memory_usage / memory_capacity

    if cpu_utilization < 0.2 and memory_utilization < 0.2:    
        problem = f"Node: {node_name} with Machine Type: {machine_type} has CPU Utilization: {cpu_utilization} and Memory Utilization: {memory_utilization}"
        prompt = "How to manage excessive use of high-performance resources in Kubernetes? Give details on how to identify and manage the high-performance resources that are underutilized. Make sure to include the steps to analyze the CPU utilization and memory usage of the high-performance resources. If there are any best practices or tools that can be used, please provide the details."
        answer = get_nlp_response(prompt)
        return problem, answer
    return None, None

def check_high_network_egress(project_id, cluster_name):    
    metric_type = 'kubernetes.io/container/network/egress_bytes_count'
    filter_ = f'metric.type="{metric_type}" AND resource.labels.cluster_name="{cluster_name}"'

    query_obj = query.Query(
        client,
        project=project_id,
        metric_type=metric_type,
        filter_=filter_,
        end_time=datetime.utcnow(),
        start_time=datetime.utcnow() - timedelta(days=1)
    )

    time_series = list(query_obj)
    for series in time_series:
        for point in series.points:
            if point.value.int64_value > 1000000000:
                problem = f"High network egress detected in cluster: {cluster_name} with value: {point.value.int64_value}"
                prompt = "How to manage high network egress in Kubernetes? Give details on how to reduce the network egress costs. Make sure to include the steps to identify the pods that are generating high network egress. If there are any best practices or tools that can be used, please provide the details."
                answer = get_nlp_response(prompt)
                return problem, answer
    return None, None 

def check_excessive_logging_and_monitoring(cluster_name): 
    logging_metric_type = 'logging.googleapis.com/byte_count'
    monitoring_metric_type = 'monitoring.googleapis.com/metric_bytes_count'

    # Create filters for the metrics
    logging_filter = f'metric.type="{logging_metric_type}" AND resource.labels.cluster_name="{cluster_name}"'
    monitoring_filter = f'metric.type="{monitoring_metric_type}" AND resource.labels.cluster_name="{cluster_name}"'

    # Create query objects to fetch time series data
    logging_query = query.Query(
        client,
        project=project_id,
        metric_type=logging_metric_type,
        filter_=logging_filter,
        end_time=datetime.utcnow(),
        start_time=datetime.utcnow() - timedelta(days=1)
    )

    monitoring_query = query.Query(
        client,
        project=project_id,
        metric_type=monitoring_metric_type,
        filter_=monitoring_filter,
        end_time=datetime.utcnow(),
        start_time=datetime.utcnow() - timedelta(days=1)
    )
 
    logging_time_series = list(logging_query)
    monitoring_time_series = list(monitoring_query) 

    for series in logging_time_series:
        for point in series.points:
            if point.value.int64_value > 100000000:
                problem = f"Excessive logging detected with value: {point.value.int64_value}"
                prompt = "How to manage excessive logging in Kubernetes? Give details on how to reduce the logging costs. Make sure to include the steps to identify the logs that are generating high frequency data points. If there are any best practices or tools that can be used, please provide the details."
                answer = get_nlp_response(prompt)
                return problem, answer

    for series in monitoring_time_series:
        for point in series.points:
            if point.value.int64_value > 100000000:
                problem = f"Excessive monitoring detected with value: {point.value.int64_value}"
                prompt = "How to manage excessive monitoring in Kubernetes? Give details on how to reduce the monitoring costs. Make sure to include the steps to identify the metrics that are generating high frequency data points. If there are any best practices or tools that can be used, please provide the details."
                answer = get_nlp_response(prompt)
                return problem, answer
    return None, None

def get_cluster_names(clusters):
    cluster_names = []
    for cluster in clusters:
        cluster_names.append(cluster['name'])
    return cluster_names




def check_kubernetes_engine():
    cluster_names = setup_kubernetes_client(clusters)
    node_capacity, node_usage = calculate_node_usage(nodes, pods)

    # Over-Provisioning of Nodes and Idle Nodes
    node_overprovisioning = node_over_provisioning(node_capacity, node_usage)

    # Excessive Use of High-Performance Resources  
    zone = "europe-west1-b"
    for cluster in clusters:
        cluster_id = cluster['name']
    node_pools = get_node_pools(project_id, zone, cluster_id)
    metrics = get_node_metrics()
    
    excessive_use_nodes = identify_excessive_high_performance_use(node_pools, metrics)

    for cluster_name in cluster_names: 
        # High Network Egress
        high_egress = check_high_network_egress(project_id, cluster_name) 

        # Excessive Logging and Monitoring
        logging_and_monitoring = check_excessive_logging_and_monitoring(cluster_name)

    results = {
        "node_overprovisioning": node_overprovisioning,
        "excessive_use_nodes": excessive_use_nodes,
        "high_egress": high_egress,
        "logging_and_monitoring": logging_and_monitoring
    }
    return results

check_kubernetes_engine()   