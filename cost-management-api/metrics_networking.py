from google.cloud import monitoring_v3
from google.oauth2 import service_account
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os 
from google.oauth2 import service_account
from openai_client import get_nlp_response
from google.cloud import logging_v2

load_dotenv()

project = os.getenv('PROJECT_ID')  
credentials = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
)
client = monitoring_v3.MetricServiceClient(credentials=credentials) 
logging_client = logging_v2.Client(credentials=credentials)
project_name = f"projects/{project}"

end_time = datetime.utcnow()
start_time = end_time - timedelta(days=1) 

interval = monitoring_v3.TimeInterval(
    {
        "end_time": {"seconds": int(end_time.timestamp()), "nanos": end_time.microsecond * 1000},
        "start_time": {"seconds": int(start_time.timestamp()), "nanos": start_time.microsecond * 1000},
    }
)

aggregation = monitoring_v3.Aggregation(
    {
        "alignment_period": {"seconds": 5 * 60},
        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
    }
) 

def get_egress_data():   
    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": 'metric.type="networking.googleapis.com/vpn_tunnel/egress_bytes_count"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            "aggregation": aggregation,
        }
    ) 
    for result in results:
        for point in result.points:
            if point.value.double_value > 1000000000:
                problem = "High Egress Data Transfer"
                prompt = "How to reduce high egress data transfer?"
                answer = get_nlp_response(prompt)
                return problem, answer
    return None, None 

def get_high_ingress_data():  
    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": 'metric.type="networking.googleapis.com/vpn_tunnel/ingress_bytes_count"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            "aggregation": aggregation,
        }
    ) 
    for result in results:
        for point in result.points:
            if point.value.double_value > 1000000000:
                problem = "High Ingress Data Transfer"
                prompt = "How to reduce high ingress data transfer? Give details on how to reduce the data transfer costs. Make sure to include the steps to identify the instances that are generating high data transfer ingress. If there are any best practices or tools that can be used, please provide the details."
                answer = get_nlp_response(prompt)
                return problem, answer
    return None, None

def get_excessive_logging(start_time, end_time, logging_client):
    log_filter = (
        f'timestamp>="{start_time.isoformat()}Z" AND timestamp<="{end_time.isoformat()}Z"'
    )

    excessive_logs = {}

    for entry in logging_client.list_entries(filter_=log_filter):
        log_name = entry.log_name
        if log_name not in excessive_logs:
            excessive_logs[log_name] = 0
        excessive_logs[log_name] += 1

    total_logs = sum(excessive_logs.values())

    if total_logs > 300:
        problem = f"Excessive Logging ({total_logs} logs)"
        prompt = (
            "How to reduce excessive logging in Google Cloud? Give details on how to reduce the frequency of logs. "
            "Make sure to include the steps to identify the logs that are generating high frequency data points. "
            "If there is any documentation that can be referred to, please provide the link. "
            "And list some other reasons why there might be an overspending problem on logging."
        )
        answer = get_nlp_response(prompt)  
        return problem, answer 
    return None, None




def check_networking():
    # High Egress Data Transfer
    high_egress_data_transfer = get_egress_data() 

    # High Ingress Data Transfer
    high_ingress_data_transfer = get_high_ingress_data()

    # Excessive Logging and Monitoring
    # excessive_logging = get_excessive_logging(start_time, end_time, logging_client) 

    results = {
        "high_egress_data_transfer": high_egress_data_transfer, 
        "high_ingress_data_transfer": high_ingress_data_transfer, 
        # "excessive_logging": excessive_logging
    }

    return results

check_networking() 